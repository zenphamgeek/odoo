try:
    from zeep.wsse.username import UsernameToken
except Exception:
    UsernameToken = None

try:
    from zeep.wsse.compose import Compose
    from zeep.wsse.signature import BinarySignature, MemorySignature, Signature
    from zeep.wsse import compose, signature, utils
except Exception:
    compose = signature = utils = Compose = BinarySignature = MemorySignature = Signature = None

