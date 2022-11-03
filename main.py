import time
import spotipy
from functools import lru_cache, wraps

"""
use this class by making an object
object = SpotDict(spotipy_authorization_token)
then use the methods as available,
object.get_liked_songs() - get all of a user's liked songs
object.get_saved_albums() - get user's saved_albums and the tracks inside
object.get_top_items() - get user's top tracks, spotify only gives 50 period. they don't save any more than that
object.get_playlsits() - gets all the data about the playlist except for the tracks inside
object.get_playlists_and_items() - this one takes the playlists and adds the tracks inside of those playlists inside of ['tracks']
                                   can be very performance/data heavy with very large playlists, consider making a maximum limit or something
                                   also very slow because spotipy isn't written in async. this means a large playlist could take 20 seconds to get
a big tip: use a dummy spotify account with some nonsense data to test your code with.
"""


class SpotDict:

    def __init__(self, auth):
        self.spot_obj = spotipy.Spotify(auth)  # you need an authetication token here, see spotify/spotipy docs
        self.spot_dict = {}  # this is a tool we'll use for later!
        self.spot_dict['user'] = self.spot_obj.current_user()  # user info, used for comparing if user is the playlist owner
        self.SLEEP_TIME = 0  # sleep time for api-call budgeting
        self.REMOVE_AVAILABLE_MARKETS = True  # available markets is a lot of data to store (over half of the text data!) so this removes all of that
        self.DEBUG_PRINT = True  # enables printing throughout the class

    def timer(func):
        @wraps(func)
        def _time_it(*args, **kwargs):
            start = int(round(time.time() * 1000))
            try:
                return func(*args, **kwargs)
            finally:
                end_ = int(round(time.time() * 1000)) - start
                print(f"Total execution time of {str(func)}: {end_ if end_ > 0 else 0} ms\n")
        return _time_it

    def remove_available_markets(self, iteration, func, x):
        try:
            iteration['items'][x]['track'].pop('available_markets')
            iteration['items'][x]['track']['album'].pop('available_markets')
            if "available_markets" not in iteration['items'][x]['track'].keys():
                if self.DEBUG_PRINT: print(f"successfully removed available_markets from {str(func)}")

        except KeyError:  # needs verification that this would be the error. however, i don't see how this would theoretically happen
            try:
                iteration['items'][x]['album'].pop('available_markets')
                if self.DEBUG_PRINT: print(f'removed available_markets from album {iteration["items"][x]["album"]["name"]}')
                for song in iteration['items'][x]['album']['tracks']['items']:
                    song.pop("available_markets")
                if self.DEBUG_PRINT: print(f'removed available_markets from songs inside album {iteration["items"][x]["album"]["name"]}')
            except KeyError:  # needs verification that this would be the error. however, i don't see how this would theoretically happen
                if 'Spotify.current_user_playlists' not in str(func):
                    if self.DEBUG_PRINT: print(f"couldn't remove available_markets from {str(func)}")
        return iteration

    @timer
    def multiple_api_calls(self, func=None, limit=50, playlist_id=None, name=None):
        # func is a variable because this exact method works for multiple information requests from spotify.
        # they have a consistent scheme that the JSON follows.

        # get how many api requests we need, round up
        if playlist_id:  # one of the few differences between playlist items and the rest
            total = self.spot_obj.playlist_tracks(playlist_id=playlist_id, limit=1)['total']
        if not playlist_id:  # normal case
            total = func(limit=1)['total']
        iterations = (int((total / limit)) + (total % limit > 0))

        longer_list = []
        song_number = 0

        for x in range(iterations):
            if playlist_id:  # for playlists, complete with printing statements
                response = self.spot_obj.playlist_tracks(playlist_id=playlist_id, limit=limit, offset=x * limit)
                if self.DEBUG_PRINT: print(f'added songs {song_number} through {song_number + limit}')
                if self.DEBUG_PRINT and self.SLEEP_TIME: print(f'waiting {self.SLEEP_TIME} seconds')
                song_number += limit  # only for printing purposes
                time.sleep(self.SLEEP_TIME)  # api budgeting

            if not playlist_id: response = func(limit=limit, offset=x * limit)

            longer_list.append(response)

        """
        looks inside of the longer_list, yoinks the ['items'], then adds them to a combined_list
        this means that we're only taking out the 'items' and putting them in the value of whatever dict key we're calling it from
        meaning that we're losing all the information that's not in ['items']. if you want this, you can still save it by
        doing something like spot_dict['key'][x] = longer_list and doing something with that info
        if none of this makes sense to you, mess around with the raw json spotify gives you and compare that with what this function gives you
        """
        combination_list = []
        if playlist_id:
            for iteration in longer_list:
                for x in range(len(iteration['items'])):
                    if self.REMOVE_AVAILABLE_MARKETS:
                        iteration['items'][x]['track'].pop('available_markets')
                        iteration['items'][x]['track']['album'].pop('available_markets')
                    combination_list.append(iteration['items'][x])
            if self.DEBUG_PRINT: print(f"added {len(combination_list)} songs from playlist {name} with playist id {playlist_id} to dict")

        if not playlist_id:
            for iteration in longer_list:
                for x in range(len(iteration['items'])):
                    if self.REMOVE_AVAILABLE_MARKETS: self.remove_available_markets(iteration, func, x)
                    combination_list.append(iteration['items'][x])
        return combination_list

    @timer
    def get_liked_songs(self):
        liked_songs = self.multiple_api_calls(func=self.spot_obj.current_user_saved_tracks, limit=50)
        if liked_songs:
            self.spot_dict['liked_songs'] = liked_songs
            if self.DEBUG_PRINT: print('added liked songs to dict')
        return liked_songs

    @timer
    def get_saved_albums(self):
        saved_albums = self.multiple_api_calls(func=self.spot_obj.current_user_saved_albums, limit=50)
        if saved_albums:
            self.spot_dict['saved_albums'] = saved_albums
            if self.DEBUG_PRINT: print('added saved albums to dict')
        return saved_albums

    @timer
    def get_top_items(self):
        top_items = self.multiple_api_calls(func=self.spot_obj.current_user_top_tracks, limit=50)
        if top_items:
            self.spot_dict['top items'] = top_items
            if self.DEBUG_PRINT: print(f'added {len(top_items)} top items to dict')
        return top_items

    @timer
    def get_playlists(self):
        self.playlists = self.multiple_api_calls(func=self.spot_obj.current_user_playlists)
        self.spot_dict['playlists'] = self.playlists
        if self.DEBUG_PRINT: print(f'added {len(self.playlists)} playlists to dict')
        return self.playlists

    # this makes a list of all the playlist_ids, purely just so we can iterate over them easier in just a second
    @timer
    def get_playlist_ids(self) -> list[str]:

        try: self.spot_dict['playlists']
        except KeyError: self.get_playlists()

        ids = []
        for idx in range(len(self.playlists)):
            ids.append(self.spot_dict['playlists'][idx]['id'])

        if self.DEBUG_PRINT: print(f'added playlist ids to dict')
        self.playlist_ids = ids
        return ids

    @timer
    def get_items_from_playlists(self, playlist_ids=None, only_add_owned_playlists=True):

        # if no playlist_ids were given, then get all of them
        if not playlist_ids: playlist_ids = self.get_playlist_ids()
        else:
            try: self.spot_dict['playlists'].index(0)
            except KeyError: self.spot_dict['playlists'] = {}
            self.playlist_ids = playlist_ids
            for iteration, id in enumerate(self.playlist_ids):
                self.spot_dict['playlists'][iteration] = self.spot_obj.playlist(playlist_id=id)
                name = self.spot_dict['playlists'][iteration]['name']
                if self.DEBUG_PRINT: print(f'added {name} to spot {iteration}')

        # take that list of playlist_ids, insert that id in multiple_api_calls_playlist(spot_obj, id)
        for id in self.playlist_ids:
            if self.DEBUG_PRINT: name = self.spot_obj.playlist(playlist_id=id)['name']

            # we need the spot_number because in ['playlists'], it's ordered from 0 up. this is the spot in which we're going to put the tracks
            spot_number = self.playlist_ids.index(id)
            if only_add_owned_playlists:
                if self.spot_dict['playlists'][spot_number]['owner']['id'] == self.spot_dict['user']['id']:
                    if self.DEBUG_PRINT: print(f'inserting tracks from {name} in slot {spot_number}')
                    self.spot_dict['playlists'][spot_number]['tracks']['tracks'] = self.multiple_api_calls(playlist_id=id, limit=100, name=name)
                else:
                    if self.DEBUG_PRINT: print(f'skipped {name}\n')
            else:
                self.spot_dict['playlists'][spot_number]['tracks']['tracks'] = self.multiple_api_calls(playlist_id=id, limit=100, name=name)
                if self.DEBUG_PRINT: print(f'inserting tracks from {name} in slot {spot_number}')
        return self.spot_dict['playlists']

    @timer
    @lru_cache
    def get_all(self):
        self.get_liked_songs()
        # self.get_saved_albums()
        # self.get_top_items()
        self.get_playlist_ids()
        self.get_items_from_playlists()
        return self.spot_dict

    @lru_cache
    def return_spot_dict(self):
        return self.spot_dict
