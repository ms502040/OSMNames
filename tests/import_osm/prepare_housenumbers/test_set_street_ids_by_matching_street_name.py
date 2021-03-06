import os
import pytest

from osmnames.database.functions import exec_sql_from_file
from osmnames.import_osm.prepare_housenumbers import set_street_ids_by_matching_street_name


@pytest.fixture(scope="function")
def schema():
    current_directory = os.path.dirname(os.path.realpath(__file__))
    exec_sql_from_file('../fixtures/test_prepare_imported_data.sql.dump', cwd=current_directory)


def test_when_street_with_same_parent_id_and_name_exists(session, schema, tables):
    session.add(tables.osm_housenumber(id=1, parent_id=1337, street="Haldenweg"))
    session.add(tables.osm_linestring(id=42, parent_id=1337, name="Haldenweg"))

    session.commit()

    set_street_ids_by_matching_street_name()

    assert session.query(tables.osm_housenumber).get(1).street_id == 42


def test_when_street_with_same_parent_id_but_different_name_exists(session, schema, tables):
    session.add(tables.osm_housenumber(id=1, parent_id=1337, street="Haldenweg"))
    session.add(tables.osm_linestring(id=42, parent_id=1337, name="Hornstrasse"))

    session.commit()

    set_street_ids_by_matching_street_name()

    assert session.query(tables.osm_housenumber).get(1).street_id is None


def test_when_street_with_same_name_but_different_parent_id_exists(session, schema, tables):
    session.add(tables.osm_housenumber(id=1, parent_id=1337, street="Haldenweg"))
    session.add(tables.osm_linestring(id=42, parent_id=9999, name="Haldenweg"))

    session.commit()

    set_street_ids_by_matching_street_name()

    assert session.query(tables.osm_housenumber).get(1).street_id is None


def test_when_merged_street_with_same_parent_id_and_name_exists(session, schema, tables):
    session.add(tables.osm_housenumber(id=1, parent_id=1337, street="Haldenweg"))
    session.add(tables.osm_linestring(id=42, merged_into=77, parent_id=1337, name="Haldenweg"))

    session.commit()

    set_street_ids_by_matching_street_name()

    assert session.query(tables.osm_housenumber).get(1).street_id == 77
