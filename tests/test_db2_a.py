
import pytest
import logging

from censere.config import Generator as thisApp
import censere.models
import censere.actions

thisApp.simulation = "00000000-0000-0000-0000-000000000000"
thisApp.astronaut_age_range = "32,45"
thisApp.solday = 1


class TestCreatingFamilies:

    # provide access to logged messages from the library calls
    # This can be used for example to see what is happening in the
    # library code by setting the libray logging to DEBUG
    # i.e. in the test functions add
    #
    #    self._caplog.set_level(logging.DEBUG)
    #
    @pytest.fixture(autouse=True)
    def add_access_to_logging(self, caplog):
        self._caplog = caplog
    

    def test_create_two_straight_male_astronauts(self, database):
        database.bind( [ censere.models.Astronaut ], bind_refs=False, bind_backrefs=False)
        database.connect( reuse_if_open=True )
        database.create_tables( [ censere.models.Astronaut ] )
        assert database.table_exists( "colonists" )

        a = censere.models.Astronaut()

        a.initialize( 1, sex='m', config=thisApp )

        # use a well known ID to make it easier to find
        a.colonist_id = "aaaaaaaa-1111-0000-0000-000000000000"
        a.orientation = 'f'

        assert a.save() == 1
        assert censere.models.Colonist.select().where( 
                    ( censere.models.Colonist.simulation == thisApp.simulation ) &
                    ( censere.models.Colonist.colonist_id == "aaaaaaaa-1111-0000-0000-000000000000" )
               ).count() == 1

        b = censere.models.Astronaut()

        b.initialize( 1, sex='m', config=thisApp )
        b.orientation = 'f'

        # use a well known ID to make it easier to find
        b.colonist_id = "aaaaaaaa-2222-0000-0000-000000000000"

        assert b.save() == 1
        assert censere.models.Colonist.select().where( 
                    ( censere.models.Colonist.simulation == thisApp.simulation ) &
                    ( censere.models.Colonist.colonist_id == "aaaaaaaa-2222-0000-0000-000000000000" )
               ).count() == 1


    def test_fail_make_one_family(self, database):
        database.bind( [ censere.models.Relationship ], bind_refs=False, bind_backrefs=False)
        database.connect( reuse_if_open=True )
        database.create_tables( [ censere.models.Relationship ] )
        assert database.table_exists( "relationships" )

        censere.actions.make_families( )

        assert censere.models.Relationship.select().count() == 0

        male1 = censere.models.Colonist.get( 
                censere.models.Colonist.colonist_id == "aaaaaaaa-1111-0000-0000-000000000000" ) 

        male2 = censere.models.Colonist.get( 
                censere.models.Colonist.colonist_id == "aaaaaaaa-2222-0000-0000-000000000000" ) 

        assert male1.state == 'single'
        assert male2.state == 'single'

    def test_create_two_straight_female_astronauts(self, database):
        database.bind( [ censere.models.Astronaut ], bind_refs=False, bind_backrefs=False)
        database.connect( reuse_if_open=True )
        database.create_tables( [ censere.models.Astronaut ] )
        assert database.table_exists( "colonists" )

        a = censere.models.Astronaut()

        a.initialize( 1, sex='f', config=thisApp )

        # use a well known ID to make it easier to find
        a.colonist_id = "aaaaaaaa-3333-0000-0000-000000000000"
        a.orientation = 'm'

        assert a.save() == 1
        assert censere.models.Colonist.select().where( 
                    ( censere.models.Colonist.simulation == thisApp.simulation ) &
                    ( censere.models.Colonist.colonist_id == "aaaaaaaa-3333-0000-0000-000000000000" )
               ).count() == 1

        b = censere.models.Astronaut()

        b.initialize( 1, sex='f', config=thisApp )
        b.orientation = 'm'

        # use a well known ID to make it easier to find
        b.colonist_id = "aaaaaaaa-4444-0000-0000-000000000000"

        assert b.save() == 1
        assert censere.models.Colonist.select().where( 
                    ( censere.models.Colonist.simulation == thisApp.simulation ) &
                    ( censere.models.Colonist.colonist_id == "aaaaaaaa-4444-0000-0000-000000000000" )
               ).count() == 1

    def test_make_one_family(self, database):
        database.bind( [ censere.models.Relationship ], bind_refs=False, bind_backrefs=False)
        database.connect( reuse_if_open=True )
        assert database.table_exists( "relationships" )

        censere.actions.make_families( )

        assert censere.models.Relationship.select().count() == 1

        assert censere.models.Colonist.select().where( 
                    ( censere.models.Colonist.state == 'couple' )
               ).count() == 2

        assert censere.models.Colonist.select().where( 
                    ( censere.models.Colonist.state == 'single' )
               ).count() == 2

    def test_make_second_family(self, database):
        database.bind( [ censere.models.Relationship ], bind_refs=False, bind_backrefs=False)
        database.connect( reuse_if_open=True )
        assert database.table_exists( "relationships" )


        censere.actions.make_families( )

        assert censere.models.Relationship.select().count() == 2

        assert censere.models.Colonist.select().where( 
                    ( censere.models.Colonist.state == 'couple' )
               ).count() == 4

        assert censere.models.Colonist.select().where( 
                    ( censere.models.Colonist.state == 'single' )
               ).count() == 0

    def test_colonist_pregnant(self, database):
        pytest.skip("Event pipeline not present yet")

    def test_maternity_leave(self, database):
        pytest.skip("Event pipeline not present yet")

    def test_colonist_born(self, database):
        database.bind( [ censere.models.Relationship ], bind_refs=False, bind_backrefs=False)
        database.connect( reuse_if_open=True )
        assert database.table_exists( "relationships" )

        # id is a hidden field - normally prefer
        # relationship_id but that is random
        family = censere.models.Relationship.get( censere.models.Relationship.id == 1 ) 

        assert family.relationship == censere.models.RelationshipEnum.partner

        first = censere.models.Colonist.get( censere.models.Colonist.colonist_id == str(family.first) )
        second = censere.models.Colonist.get( censere.models.Colonist.colonist_id == str(family.second) )

        mother = None
        father = None

        assert first.sex != second.sex

        if first.sex == 'm':
            father = first.colonist_id
            mother = second.colonist_id
        else:
            mother = first.colonist_id
            father = second.colonist_id

        kwargs = { "biological_mother" : mother, "biological_father": father }

        # Call main processing code to create a new born person
        censere.events.callbacks.colonist_born( **kwargs )

        assert censere.models.Colonist.select().count() == 5

        child = censere.models.Colonist.get( censere.models.Colonist.birth_solday == thisApp.solday )

        assert child.biological_father == father
        assert child.biological_mother == mother

        # mother and father both have a child relationship
        assert censere.models.Relationship.select().where( 
                    ( censere.models.Relationship.relationship == censere.models.RelationshipEnum.child )
               ).count() == 2

    def test_start_paternity_leave(self, database):
        pytest.skip("Event pipeline not present yet")

    def test_end_paternity_leave(self, database):
        pytest.skip("Event pipeline not present yet")

    def test_end_maternity_leave(self, database):
        pytest.skip("Event pipeline not present yet")

    def test_close_database(self, database):

        database.close()
