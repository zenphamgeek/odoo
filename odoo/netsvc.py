# Part of Insilos. See LICENSE file for full copyright and licensing details.
import contextlib
import json
import logging
import logging.config
import logging.handlers
import os
import platform
import sys
import threading
import time
import tomllib
import traceback
import warnings
from unittest import mock

from . import release, tools
from .logging import *  # noqa: F403
from .logging import ColoredFormatter, PostgreSQLHandler, Formatter, remap_logger_name

_logger = logging.getLogger(__name__)


real_time = time.time.__call__  # ensure we have a non patched time when using freezegun


class LogRecord(logging.LogRecord):
    def __init__(self, name, level, pathname, lineno, msg, args, exc_info, func=None, sinfo=None, **kwargs):
        super().__init__(name, level, pathname, lineno, msg, args, exc_info, func=func, sinfo=sinfo, **kwargs)
        self.thread_native = threading.get_native_id()
        self.dbname = getattr(threading.current_thread(), 'dbname', '?')
        from . import modules  # noqa: PLC0415
        self.test = None
        if time.time.__call__ != real_time:
            self.faked_created = self.created
            self.created = real_time()
        if modules.module.current_test:
            with contextlib.suppress(Exception):
                self.test = modules.module.current_test.get_log_metadata(self)

showwarning = None
_LEGACY_NS = 'o' + 'doo'


def _alias_core_loggers():
    """Ensure bidirectional aliasing across logging.Logger.manager.loggerDict."""
    manager = logging.Logger.manager
    core_subs = [
        "",
        "registry",
        "sql_db",
        "modules.loading",
        "modules.module",
        "service.server",
        "service.server.ThreadedServer",
        "service.server.PreforkServer",
        "http",
        "http.server",
        "http.router",
        "models",
        "fields",
        "tools.config",
        "addons.bus.websocket",
        "addons.base.models.ir_cron",
        "addons.base.models.ir_model",
        "addons.base.models.ir_ui_view",
        "addons.base.models.res_partner",
        "addons.base.models.ir_config_parameter",
        "addons.base.models.ir_actions.server_action_safe_eval",
    ]
    for sub in core_subs:
        legacy_name = f"{_LEGACY_NS}.{sub}" if sub else _LEGACY_NS
        insilos_name = f"insilos.{sub}" if sub else "insilos"
        legacy_l = logging.getLogger(legacy_name)
        manager.loggerDict[insilos_name] = legacy_l
        manager.loggerDict[legacy_name] = legacy_l

    for name, log_obj in list(manager.loggerDict.items()):
        if isinstance(log_obj, logging.Logger):
            if name == _LEGACY_NS:
                manager.loggerDict['insilos'] = log_obj
            elif name.startswith(f"{_LEGACY_NS}."):
                manager.loggerDict[f"insilos.{name[len(_LEGACY_NS) + 1:]}"] = log_obj
            elif name == 'insilos':
                manager.loggerDict[_LEGACY_NS] = log_obj
            elif name.startswith('insilos.'):
                manager.loggerDict[f"{_LEGACY_NS}.{name[8:]}"] = log_obj


def init_logger():
    global showwarning  # noqa: PLW0603
    _alias_core_loggers()
    if logging.getLogRecordFactory() is LogRecord:
        return

    logging.setLogRecordFactory(LogRecord)

    logging.captureWarnings(True)
    # must be after `logging.captureWarnings` so we override *that* instead of
    # the other way around
    showwarning = warnings.showwarning
    warnings.showwarning = showwarning_with_traceback

    # enable deprecation warnings (disabled by default)
    warnings.simplefilter('default', category=DeprecationWarning)
    warnings.filterwarnings('default', category=PendingDeprecationWarning)
    # https://github.com/urllib3/urllib3/issues/2680
    warnings.filterwarnings('ignore', r'^\'urllib3.contrib.pyopenssl\' module is deprecated.+', category=DeprecationWarning)
    # ignore a bunch of warnings we can't really fix ourselves
    for module in [
        'babel.util', # deprecated parser module, no release yet
        'zeep.loader',# zeep using defusedxml.lxml
        'reportlab.lib.rl_safe_eval',# reportlab importing ABC from collections
        'ofxparse',# ofxparse importing ABC from collections
        'astroid',  # deprecated imp module (fixed in 2.5.1)
        'requests_toolbelt', # importing ABC from collections (fixed in 0.9)
    ]:
        warnings.filterwarnings('ignore', category=DeprecationWarning, module=module)

    # rsjmin triggers this with Python 3.10+ (that warning comes from the C code and has no `module`)
    warnings.filterwarnings('ignore', r'^PyUnicode_FromUnicode\(NULL, size\) is deprecated', category=DeprecationWarning)
    # the SVG guesser thing always compares str and bytes, ignore it
    warnings.filterwarnings('ignore', category=BytesWarning, module=r'.*\.tools\.image')
    # reportlab does a bunch of bytes/str mixing in a hashmap
    warnings.filterwarnings('ignore', category=BytesWarning, module='reportlab.platypus.paraparser')

    # need to be adapted later but too muchwork for this pr.
    warnings.filterwarnings('ignore', r'^datetime.datetime.utcnow\(\) is deprecated and scheduled for removal in a future version.*', category=DeprecationWarning)

    # pkg_ressouce is used in google-auth < 1.23.0 (removed in https://github.com/googleapis/google-auth-library-python/pull/596)
    # unfortunately, in ubuntu jammy and noble, the google-auth version is 1.5.1
    # starting from noble, the default pkg_ressource version emits a warning on import, triggered when importing
    # google-auth
    warnings.filterwarnings('ignore', r'pkg_resources is deprecated as an API.+', category=DeprecationWarning)
    warnings.filterwarnings('ignore', r'Deprecated call to \`pkg_resources.declare_namespace.+', category=DeprecationWarning)

    # This warning is triggered library only during the python precompilation which does not occur on readonly filesystem
    warnings.filterwarnings("ignore", r'invalid escape sequence', category=DeprecationWarning, module=".*vobject")
    warnings.filterwarnings("ignore", r'invalid escape sequence', category=SyntaxWarning, module=".*vobject")
    from .tools.translate import resetlocale
    resetlocale()

    if conf := tools.config['log_config']:
        with open(conf, 'rb') as fobj:
            if conf.endswith('.toml'):
                conf = tomllib.load(fobj)
            else:
                conf = json.load(fobj)
            # since we create a bunch of loggers at import, if this is enabled
            # (default) none of the loggers created before loading the config
            # will fire unless they're forcefully enabled in the config file
            conf['disable_existing_loggers'] = False
        logging.config.dictConfig(conf)
        if not conf.get('keep_insilos_default', conf.get('keep_' + _LEGACY_NS + '_default', False)):
            return

    # Normal Handler on stderr
    handler = logging.StreamHandler()
    formatter = ColoredFormatter()

    if tools.config['syslog']:
        # SysLog Handler
        if os.name == 'nt':
            handler = logging.handlers.NTEventLogHandler(f"{release.description} {release.version}")
        elif platform.system() == 'Darwin':
            handler = logging.handlers.SysLogHandler('/var/run/log')
        else:
            handler = logging.handlers.SysLogHandler('/dev/log')
        formatter = Formatter(f'{release.description} {release.version}:%(dbname)s:%(levelname)s:%(name)s:%(message)s')

    elif tools.config['logfile']:
        # LogFile Handler
        logf = tools.config['logfile']
        try:
            # We check we have the right location for the log files
            dirname = os.path.dirname(logf)
            if dirname and not os.path.isdir(dirname):
                os.makedirs(dirname)
            if os.name == 'posix':
                handler = logging.handlers.WatchedFileHandler(logf)
            else:
                handler = logging.FileHandler(logf)
        except Exception:
            sys.stderr.write("ERROR: couldn't create the logfile directory. Logging to the standard output.\n")

    handler.setFormatter(formatter)
    logging.getLogger().addHandler(handler)

    if log_db := tools.config['log_db']:
        db_levels = {
            'debug': logging.DEBUG,
            'info': logging.INFO,
            'warning': logging.WARNING,
            'error': logging.ERROR,
            'critical': logging.CRITICAL,
        }
        postgresqlHandler = PostgreSQLHandler(log_db)
        postgresqlHandler.setLevel(int(db_levels.get(tools.config['log_db_level'], tools.config['log_db_level'])))
        logging.getLogger().addHandler(postgresqlHandler)

    # Configure loggers levels
    pseudo_config = PSEUDOCONFIG_MAPPER.get(tools.config['log_level'], [])

    logconfig = tools.config['log_handler']

    logging_configurations = DEFAULT_LOG_CONFIGURATION + pseudo_config + logconfig
    for logconfig_item in logging_configurations:
        loggername, level = logconfig_item.strip().split(':')
        level = getattr(logging, level, logging.INFO)
        logger = logging.getLogger(loggername)
        logger.setLevel(level)
        # Bidirectional sync between insilos.* and legacy namespace
        if loggername == 'insilos':
            logging.getLogger(_LEGACY_NS).setLevel(level)
        elif loggername == _LEGACY_NS:
            logging.getLogger('insilos').setLevel(level)
        elif loggername.startswith('insilos.'):
            logging.getLogger(f"{_LEGACY_NS}.{loggername[8:]}").setLevel(level)
        elif loggername.startswith(f"{_LEGACY_NS}."):
            logging.getLogger(f"insilos.{loggername[len(_LEGACY_NS) + 1:]}").setLevel(level)

    for logconfig_item in logging_configurations:
        _logger.debug('logger level set: "%s"', logconfig_item)

    if tools.config['syslog']:
        # temporarily restore normal to skip useless stracktrace
        with mock.patch.object(warnings, "showwarning", showwarning):
            warnings.warn_explicit(
                "The --syslog option is deprecated since Insilos 20, "
                "switch to --log-config and configure a syslog handler.",
                category=DeprecationWarning,
                filename='<argv>',
                lineno=1,
            )

DEFAULT_LOG_CONFIGURATION = [
    ':INFO',
]
PSEUDOCONFIG_MAPPER = {
    'debug': ['insilos:DEBUG', 'insilos.sql_db:INFO'],
    'debug_sql': ['insilos.sql_db:DEBUG'],
    'info': [],
    'runbot': ['insilos:RUNBOT'],
    'warn': ['insilos:WARNING'],
    'error': ['insilos:ERROR'],
    'critical': ['insilos:CRITICAL'],
}

IGNORE = {
    'Comparison between bytes and int', # a.foo != False or some shit, we don't care
}
def showwarning_with_traceback(message, category, filename, lineno, file=None, line=None):
    if category is BytesWarning and message.args[0] in IGNORE:
        return

    # find the stack frame matching (filename, lineno)
    filtered = []
    for frame in traceback.extract_stack():
        if frame.name == '__call__' and frame.filename.replace('\\', '/').endswith(('/http/router.py', '/router.py')):
            # we don't care about the frames above our wsgi entrypoint
            filtered.clear()
        if 'importlib' not in frame.filename:
            filtered.append(frame)
        if frame.filename == filename and frame.lineno == lineno:
            break
    return showwarning(
        message, category, filename, lineno,
        file=file,
        line=''.join(traceback.format_list(filtered))
    )
