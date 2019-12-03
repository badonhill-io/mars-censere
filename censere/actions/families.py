
import logging
import random
import uuid

import peewee

from censere.config import Generator as thisApp

import censere.models as MODELS

import censere.utils as UTILS

import censere.events.store as EVENTS
import censere.events.callbacks as CALLBACKS

##
# Make a single new family out of two singles
# the caller is responsible for calling this at
# appropriate times...
def make( ):

    #logging.info( '%d.%d (%d) Trying to make a new family', *UTILS.from_soldays( thisApp.solday ), thisApp.solday )

    partner = MODELS.Colonist.alias()
    
    # TODO how to avoid "incest" ?
    query = MODELS.Colonist.select( 
            MODELS.Colonist.colonist_id.alias('userid1'),
            partner.colonist_id.alias('userid2'), 
            MODELS.Colonist.first_name.alias('first_name1'),
            partner.first_name.alias('first_name2'),
            MODELS.Colonist.family_name.alias('family_name1'),
            partner.family_name.alias('family_name2'),
            MODELS.Colonist.sex.alias('sex1'),
            partner.sex.alias('sex2')
        ).join(
            partner, on=( partner.simulation == MODELS.Colonist.simulation ), attr="partner" 
        ).where(
                # no self-partnering
                ( MODELS.Colonist.colonist_id != partner.colonist_id ) &
                # - both persons must be single - so currently no extended families
                ( MODELS.Colonist.state == 'single' ) &
                ( partner.state == 'single' ) &
                # compatible sexuality
                ( MODELS.Colonist.orientation.contains( partner.sex ) ) &
                ( partner.orientation.contains( MODELS.Colonist.sex ) ) &
                # both over 18 earth years years
                ( MODELS.Colonist.birth_solday < thisApp.solday - ( 18 * 365.25 * 1.02749125 ) ) &
                ( partner.birth_solday < thisApp.solday - ( 18 * 365.25 * 1.02749125 ) ) &
                # still alive
                ( MODELS.Colonist.death_solday == 0 ) &
                ( partner.death_solday == 0 ) &
                # part of this execution run
                ( MODELS.Colonist.simulation == thisApp.simulation ) &
                ( partner.simulation == thisApp.simulation )
            ).order_by( 
                peewee.fn.random() 
            ).limit(1).dicts()
    
    for row in query.execute():

        # rely on triggers to update colonist state to couple 

        r = MODELS.Relationship()

        r.relationship_id=str(uuid.uuid4())
        r.first=row['userid1']
        r.second=row['userid2']
        r.relationship=MODELS.RelationshipEnum.partner
        r.begin_solday=thisApp.solday

        logging.info( '%d.%d Creating family between %s %s and %s %s',
            *UTILS.from_soldays( thisApp.solday ),
            row['first_name1'], row['family_name1'], row['first_name2'], row['family_name2'] )

        r.save()

        # TODO add a callback to randomly break the relationship
        # here (after some random time) or handle it in the main loop ???

        # TODO similar vein - do we handle children here or in main loop ???
        #
        # Doing it here allows us to make children event based - registering next steps
        # when a step completes and we don't have to handle "cool off" state as
        # a special case 

        # basic pregnancy steps might be:
        #   reduce productivity after Y months
        #   maternity leave after 8 - for X time
        #   reset productivity after Z as ML ends
        #   paternity leave ? what impact for "frontier" colony ?
        # those should all be configurable - we don't trigger them all here
        # so that we can model early failures (mothers death or miscariages)

        mother=None
        father=None
        if row['sex1'] != row['sex2']:
            if row['sex1'] == "f":
                mother = row['userid1']
                father = row['userid2']
            else:
                mother = row['userid2']
                father = row['userid1']
        else:
            # TODO - this needs to handle surrogate mothers (and fathers)
            pass

        if mother and father:
            # TODO
            # This should take into account mothers age.
            # dramtic falloff in fertility after 35 ???
            # radiation impact ???
            if random.randrange(0,99) < 40:

                birth_day = thisApp.solday + random.randrange( 400, 1100)

                logging.info( '%d.%d %s %s and %s %s are expecting a child on %d.%d',
                    *UTILS.from_soldays( thisApp.solday ),
                    row['first_name1'], row['family_name1'], row['first_name2'], row['family_name2'],
                    *UTILS.from_soldays( birth_day )
                )

                # register a function to be called at `when`
                EVENTS.register_callback( 
                    when= birth_day,
                    callback_func=CALLBACKS.colonist_born,
                    kwargs= { "biological_mother" : mother, "biological_father": father }
                )

            else:

                EVENTS.register_callback( 
                    when= thisApp.solday + random.randrange( 1, 760),
                    callback_func=CALLBACKS.end_relationship,
                    kwargs= { "relationship_id" : r.relationship_id }
                )

##
# break up a family (while partners are alive)
# clearing up a family where one member dies is handled
# in the database layer (models/triggers.py)
def breakup( ):
    pass