from organizer.core import Preferences, PreferencesStore


def test_defaults_are_returned_when_user_has_no_prefs():
    store = PreferencesStore()
    prefs = store.get("user-1")

    assert prefs.favorite_city == "Warszawa"
    assert prefs.budget_pln_per_night == 300
    assert prefs.category == "any"


def test_can_save_and_load_preferences():
    store = PreferencesStore()
    custom = Preferences(favorite_city="Kraków", budget_pln_per_night=450, category="music")

    store.set("pawel", custom)
    loaded = store.get("pawel")

    assert loaded == custom
    assert loaded.favorite_city == "Kraków"
    assert loaded.budget_pln_per_night == 450
    assert loaded.category == "music"


def test_update_changes_only_selected_fields():
    store = PreferencesStore()

    # start: defaulty
    updated = store.update("u1", favorite_city="Gdańsk")

    assert updated.favorite_city == "Gdańsk"
    assert updated.budget_pln_per_night == 300   # bez zmian
    assert updated.category == "any"             # bez zmian

    updated2 = store.update("u1", budget_pln_per_night=200, category="food")
    assert updated2.favorite_city == "Gdańsk"
    assert updated2.budget_pln_per_night == 200
    assert updated2.category == "food"
