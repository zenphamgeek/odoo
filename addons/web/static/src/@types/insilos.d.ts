interface InsilosModuleErrors {
    cycle?: string | null;
    failed?: Set<string>;
    missing?: Set<string>;
    unloaded?: Set<string>;
}
type OdooModuleErrors = InsilosModuleErrors;

interface InsilosModuleFactory {
    deps: string[];
    fn: InsilosModuleFactoryFn;
    ignoreMissingDeps: boolean;
}
type OdooModuleFactory = InsilosModuleFactory;

type InsilosModule = Record<string, any>;
type OdooModule = InsilosModule;

type InsilosModuleFactoryFn = (require: (dependency: string) => InsilosModule) => InsilosModule;
type OdooModuleFactoryFn = InsilosModuleFactoryFn;

class InsilosModuleLoader {
    bus: EventTarget;
    checkErrorProm: Promise<void> | null;
    debug: boolean;
    /**
     * Mapping [name => factory]
     */
    factories: Map<string, InsilosModuleFactory>;
    /**
     * Names of failed modules
     */
    failed: Set<string>;
    /**
     * Names of modules waiting to be started
     */
    jobs: Set<string>;
    /**
     * Mapping [name => module]
     */
    modules: Map<string, InsilosModule>;

    constructor(root?: HTMLElement);
    addJob: (name: string) => void;
    define: (
        name: string,
        deps: string[],
        factory: InsilosModuleFactoryFn,
        lazy?: boolean
    ) => InsilosModule;
    findErrors: (jobs?: Iterable<string>) => InsilosModuleErrors;
    findJob: () => string | null;
    reportErrors: (errors: InsilosModuleErrors) => Promise<void>;
    require: (dependency: string) => InsilosModule;
    sortFactories: () => void;
    startModule: (name: string) => InsilosModule;
    startModules: () => void;
}
type OdooModuleLoader = InsilosModuleLoader;

declare const insilos: {
    csrf_token: string;
    debug: string;
    define: InsilosModuleLoader["define"];
    loader: InsilosModuleLoader;
    translationContext?: string;
};
