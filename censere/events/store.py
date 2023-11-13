
import importlib
import logging
import json

from censere.config import thisApp

import censere.utils as UTILS

import censere.models as MODELS

import censere.db as DB

LOGGER = logging.getLogger("c.e.store")
DEVLOG = logging.getLogger("d.devel")

##
# \param when - absolute solday to execute the function.
# \param callback_func - fully qualified function
def register_callback( when=0, order=20, periodic=0, name="", callback_func=None, kwargs=None ):

    if when == 0 or callback_func == None:

        logging.error("Missing required arguments in call to register_callback()")

        return

    if periodic == 0:
        LOGGER.log( thisApp.DETAIL, "%d.%03d Registering %s() to be run once on %d (%d.%d)", *UTILS.from_soldays( thisApp.solday ), callback_func.__name__, when, *UTILS.from_soldays( when ) )
    else:
        LOGGER.log( thisApp.DETAIL, "%d.%03d Registering %s() to be run every %d Sols starting on %d (%d.%d)", *UTILS.from_soldays( thisApp.solday ), callback_func.__name__, periodic, when, *UTILS.from_soldays( when ) )

    try:
        idx = MODELS.Event.select().where(
            ( MODELS.Event.simulation_id == thisApp.simulation ) &
            ( MODELS.Event.when == when ) &
            ( MODELS.Event.callback_func == "{}.{}".format( callback_func.__module__, callback_func.__name__ ) )
        ).count()

        e = MODELS.Event()

        e.simulation_id = thisApp.simulation
        e.registered = thisApp.solday
        e.when = when
        e.order = order
        e.periodic = periodic
        e.idx = idx
        # This allows us to pass a real function into the register function (rather then a string)
        # but store the full name of the function for later execution
        e.callback_func = "{}.{}".format( callback_func.__module__, callback_func.__name__ )
        e.args =  json.dumps( kwargs )

        e.save()
    except Exception as e:
        LOGGER.log( logging.FATAL, "%d.%03d Failed to register callback %s() to be run at %d (%d.%d)", *UTILS.from_soldays( thisApp.solday ), callback_func, when, *UTILS.from_soldays( when ) )
        LOGGER.error( str(e))


def invoke_callbacks( ):
    """Invoke callbacks register for the current Sol day"""

    LOGGER.info( '%d.%03d Processing scheduled events', *UTILS.from_soldays( thisApp.solday ) )

    query = MODELS.Event.select(
        MODELS.Event.callback_func,
        MODELS.Event.idx,
        MODELS.Event.args
    ).filter(
        ( MODELS.Event.simulation_id == thisApp.simulation ) &
        ( 
          ( MODELS.Event.when == thisApp.solday ) | ( thisApp.solday > MODELS.Event.when ) & ( ( MODELS.Event.periodic > 0 ) & ( DB.mod(thisApp.solday, MODELS.Event.periodic) == 0 ) )
        )
    ).order_by(
        MODELS.Event.order,
        MODELS.Event.id,
        MODELS.Event.idx
    )

    for row in query.execute():

        try:
            mod_name, func_name = row.callback_func.rsplit('.',1)

            LOGGER.log( logging.INFO, '%d.%03d   Calling %s()', *UTILS.from_soldays( thisApp.solday ), func_name )


            mod = importlib.import_module(mod_name)

            kwargs = json.loads( row.args )

            kwargs['idx'] = row.idx

            func = getattr(mod, func_name)

            LOGGER.log( logging.DEBUG, "%d.%03d Invoking callback %s( %s )", *UTILS.from_soldays( thisApp.solday ), row.callback_func, kwargs )

            result = func( **kwargs )

        except Exception as e:
            LOGGER.exception( '%d.%03d Failure during invocation of event callback %s(): %s )', *UTILS.from_soldays( thisApp.solday ), row.callback_func, str(e) )





