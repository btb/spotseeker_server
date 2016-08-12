"""A cache that stores spot JSON representations in memory for fast loading"""
from spotseeker_server.models import Spot


spots_cache = {}


def get_spots(spots):
    """Retrieves a list of spots from the cache."""
    try:
        if len(spots_cache.values()) == 0:
            load_spots()

        spot_dicts = []
        for spot in spots:
            if spot.id not in spots_cache:
                cache_spot(spot)

            spot_dicts.append(spots_cache[spot.id])

        return spot_dicts
    except Exception as ex:
        print "Exception!: " + str(ex)


def get_all_spots():
    """Returns all spots stored in the cache."""
    all_spots = []
    for spot in spots_cache.values():
        all_spots.append(spot)
    return all_spots


def load_spots():
    """
    Loads all spots from the database and stores their JSON representations in
    the memory cache.
    """
    spots = Spot.objects.all()
    for spot in spots:
        spots_cache[spot.id] = spot.json_data_structure()


def cache_spot(spot_model):
    """Sets the cache of a spot."""
    spots_cache[spot_model.id] = spot_model.json_data_structure()


def delete_spot(spot_model):
    """Removes a specific spot from the cache"""
    if spot_model.id in spots_cache:
        del spots_cache[spot_model.id]


def clear_cache():
    """Clears the cache."""
    spots_cache.clear()
