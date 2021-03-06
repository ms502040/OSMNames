import pytest
import os

from geoalchemy2.elements import WKTElement
from osmnames.database.functions import exec_sql_from_file
from osmnames.import_osm import import_osm


@pytest.fixture(scope="module")
def schema():
    current_directory = os.path.dirname(os.path.realpath(__file__))
    exec_sql_from_file('fixtures/test_prepare_imported_data.sql.dump', cwd=current_directory)


def test_name_get_set_from_all_tags(session, schema, tables):
    session.add(tables.osm_polygon(id=1, name="", all_tags={"name:en":"Zurich"}))
    session.add(tables.osm_linestring(id=1, name="", all_tags={"name:de":"Rhein"}))
    session.commit()

    import_osm.set_names()

    assert session.query(tables.osm_polygon).get(1).name == "Zurich"
    assert session.query(tables.osm_linestring).get(1).name == "Rhein"


def test_name_get_set_according_to_priority(session, schema, tables):
    # Where priority order is en, fr, de, es, ru, zh

    session.add(
    	tables.osm_polygon(
			id=2,
			name="",
			all_tags={"name:fr":"Lac Leman","name:de":"Genfersee","name:en":"Lake Geneva"}
		)
    )
    session.add(
    	tables.osm_linestring(
			id=2,
			name="",
			all_tags={"name:es":"Rin","name:it":"Reno","name:de":"Rhein"}
		)
    )
    session.commit()
    import_osm.set_names()

    assert session.query(tables.osm_polygon).get(2).name == "Lake Geneva"
    assert session.query(tables.osm_linestring).get(2).name == "Rhein"


def test_alternative_names_get_set(session, schema, tables):
    session.add(
        tables.osm_point(
            id=1,
            all_tags={"name:de":"Matterhorn","name:fr":"Cervin","name:it":"Cervino"}
        )
    )
    session.commit()
    import_osm.set_names()

    alternative_names = session.query(tables.osm_point).get(1).alternative_names

    assert all(x in alternative_names for x in ["Matterhorn", "Cervin", "Cervino"])


def test_alternative_names_do_not_contain_name(session, schema, tables):
    session.add(
        tables.osm_point(
            id=2,
            name="Matterhorn",
            all_tags={"name:de":"Matterhorn","name:fr":"Cervin","name:it":"Cervino"}
        )
    )
    session.commit()
    import_osm.set_names()

    assert "Matterhorn" not in session.query(tables.osm_point).get(2).alternative_names


def test_alternative_names_do_not_contain_duplicates(session, schema, tables):
    session.add(
        tables.osm_point(
            id=3,
            name="Matterhorn",
            all_tags={"name:fr":"Cervin","name:it":"Cervino","alt_name":"Cervino"}
        )
    )
    session.commit()
    import_osm.set_names()

    assert session.query(tables.osm_point).get(3).alternative_names.count("Cervino") == 1


def test_alternative_names_are_empty_if_only_name_is_present(session, schema, tables):
    session.add(
        tables.osm_point(
            id=4,
            name="Matterhorn"
        )
    )
    session.commit()
    import_osm.set_names()

    assert session.query(tables.osm_point).get(4).alternative_names == ''


def test_tabs_get_deleted_from_name(session, schema, tables):
    session.add(
        tables.osm_polygon(
            id=3,
            name="Lake\t\tZurich"
            )
        )
    session.commit()
    import_osm.set_names()

    assert session.query(tables.osm_polygon).get(3).name == "Lake Zurich"


def test_tabs_get_deleted_from_alternative_names(session, schema, tables):
    session.add(
        tables.osm_polygon(
            id=4,
            name = 'Bodensee',
            all_tags={"name:en":"Lake         Constance","name:fr":"Lac\tde\tConstance" }            
            )
        )
    session.commit()
    import_osm.set_names()

    assert session.query(tables.osm_polygon).get(4).alternative_names.count('\t') == 0
