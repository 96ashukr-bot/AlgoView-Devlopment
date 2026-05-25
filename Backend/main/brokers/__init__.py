from main.brokers.base import BaseBroker, BaseBrokerAdapter


def get_broker_adapter(*args, **kwargs):
    from main.brokers.registry import get_broker_adapter as registry_get_broker_adapter

    return registry_get_broker_adapter(*args, **kwargs)


def __getattr__(name):
    if name == "BROKER_ADAPTERS":
        from main.brokers.registry import BROKER_ADAPTERS

        return BROKER_ADAPTERS
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["BaseBroker", "BaseBrokerAdapter", "BROKER_ADAPTERS", "get_broker_adapter"]
