from typing import Callable
from functools import lru_cache, wraps
import time
import spotipy

class SpotDict:
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

    def __init__(self, auth):
        self.spot_obj: spotipy.Spotify = spotipy.Spotify(auth)  # you need an authetication token here, see spotify/spotipy docs
        self.spot_dict: dict = {}  # this is a tool we'll use for later!
        self.spot_dict['user']: dict = self.spot_obj.current_user()  # user info, used for comparing if user is the playlist owner
        self.spot_dict['playlists']: dict = {} #make this dict always available in case you run get_playlists_and_items() first
        self.sleep_time: int = 0  # sleep time for api-call budgeting
        self.remove_available_markets: bool = True  # available markets is a lot of data to store (over half of the text data!) so this removes all of that
        self.debug_print:bool = True  # enables printing throughout the class

    @staticmethod
    def timer(func):
        """times the function calls for debugging. this is a decorator"""
        @wraps(func)
        def _time_it(*args, **kwargs):
            start = int(round(time.time() * 1000))
            try:
                return func(*args, **kwargs)
            finally:
                end_ = int(round(time.time() * 1000)) - start
                print(f"Total execution time of {str(func)}: {end_ if end_ > 0 else 0} ms\n")
        return _time_it

    def _remove_available_markets(self, iteration, func, x):
        try:
            iteration['items'][x]['track'].pop('available_markets')
            iteration['items'][x]['track']['album'].pop('available_markets')
            if "available_markets" not in iteration['items'][x]['track'].keys():
                if self.debug_print: 
                    print(f"successfully removed available_markets from {str(func)}")

        except KeyError:  
            #if the iteration comes from saved_albums, the avaiable_markets key is in a different place.
            try:
                iteration['items'][x]['album'].pop('available_markets')
                for song in iteration['items'][x]['album']['tracks']['items']:
                    song.pop("available_markets")

                if self.debug_print: 
                    print(f'removed available_markets from album {iteration["items"][x]["album"]["name"]}')
                    print(f'removed available_markets from songs inside album {iteration["items"][x]["album"]["name"]}')

            except KeyError:  # needs verification that this would be the error. however, i don't see how this would theoretically happen
                if 'Spotify.current_user_playlists' not in str(func):
                    if self.debug_print: 
                        print(f"couldn't remove available_markets from {str(func)}")

        return iteration

    @timer
    def _pagination(self,
                    func: Callable = None,
                    limit: int = 50) -> list:

        """takes the function and does the spotify api call.
           all other methods point to this one, making it dry.
           it's a little messy because getting playlist_items returns
           in a different format than all the other calls."""

        total = func(limit=1)['total']
        iterations = (int((total / limit)) + (total % limit > 0))
        songs, items = [], []

        for iteration in range(iterations):
            response = func(limit=limit, 
                            offset=iteration * limit)
            items.append(response)

        for iteration in items:
            for idx in range(len(iteration['items'])):
                if self.remove_available_markets:
                    self._remove_available_markets(iteration, func, idx)
                songs.append(iteration['items'][idx])
        return songs

    @timer
    def _playlist_item_pagination(self,
                                  playlist_id: str,
                                  limit: int = 100,
                                  ) -> list:
        """pagination for playlist items. only a little different.
           songs is only the song data, items has the song and some other
           metadata that spotify keeps other than the song. if you want this
           data, return the items list instead of songs. 
           i don't have a need for items, so i've left it out."""

        songs, items = [], []

        total = self.spot_obj.playlist_tracks(playlist_id=playlist_id, limit=1)['total']
        iterations = (int((total / limit)) + (total % limit > 0))

        for iteration in range(iterations):
            response = self.spot_obj.playlist_tracks(playlist_id=playlist_id,
                                                 limit=limit,
                                                 offset=iteration * limit
                                                 )
            items.append(response)

            if self.debug_print: 
                print(f'added songs {iteration + limit} through {iteration * limit + limit}')
                if self.sleep_time:
                    print(f'waiting {self.sleep_time} seconds')

        time.sleep(self.sleep_time)  # api budgeting

        for iteration in items:
            for idx in range(len(iteration['items'])):
                if self.remove_available_markets:
                    iteration['items'][idx]['track'].pop('available_markets')
                    iteration['items'][idx]['track']['album'].pop('available_markets')
                songs.append(iteration['items'][idx])
        if self.debug_print: 
            print(f"added {len(songs)} songs in playist id {playlist_id} to dict")

    @timer
    def get_liked_songs(self) -> dict:
        """get liked songs"""
        liked_songs = self._pagination(func=self.spot_obj.current_user_saved_tracks, limit=50)
        if liked_songs:
            self.spot_dict['liked_songs'] = liked_songs
            if self.debug_print: print('added liked songs to dict')
        return liked_songs

    @timer
    def get_saved_albums(self) -> dict:
        """get saved albums"""
        saved_albums = self._pagination(func=self.spot_obj.current_user_saved_albums, limit=50)
        if saved_albums:
            self.spot_dict['saved_albums'] = saved_albums
            if self.debug_print: print('added saved albums to dict')
        return saved_albums

    @timer
    def get_top_items(self) -> dict:
        """get top items (50 max)"""
        top_items = self._pagination(func=self.spot_obj.current_user_top_tracks, limit=50)
        if top_items:
            self.spot_dict['top items'] = top_items
            if self.debug_print: 
                print(f'added {len(top_items)} top items to dict')
        return top_items

    @timer
    def get_playlists(self) -> dict:
        """get playlists details, without the songs attached"""
        playlists = self._pagination(func=self.spot_obj.current_user_playlists)
        self.spot_dict['playlists'] = playlists
        if self.debug_print: 
            print(f'added {len(playlists)} playlists to dict')
        return playlists

    @timer
    def get_items_from_playlists(self,
                                 playlist_ids: list = None,
                                 only_add_owned_playlists: bool = True
                                 ) -> dict:
        """if playlist_ids is None, it will get all the playlists in a profile and add their tracks.
           if playlist_ids is a list, it will only get the tracks from those playlists.
           if only_add_owned_playlists is True, it will only add the tracks from playlists where the user id and the playlist owner id match.
           the if/else catches are a little messy, try to ignore the if debug_prints, then it's much simpler"""

        if playlist_ids: # if playlist_ids is given, only get those playlist items
            for iteration, playlist_id in enumerate(playlist_ids):
                self.spot_dict['playlists'][iteration] = self.spot_obj.playlist(playlist_id=playlist_id)

                if self.debug_print:
                    print(f"added {self.spot_dict['playlists'][iteration]['name']} to spot {iteration}")

        else: # if playlist_ids is not given, get all the playlists in a profile
            playlists = self.spot_dict['playlists']
            if len(playlists) == 0: # if there are no playlists in the dict, get them
                self.get_playlists()
            playlist_ids = []
            for idx in range(len(playlists)):
                playlist_ids.append(self.spot_dict['playlists'][idx]['id'])

            if self.debug_print:
                print(f'added {len(playlist_ids)} playlist ids to dict')

        # take that list of playlist_ids, insert that id in multiple_api_calls_playlist(spot_obj, id)
        for playlist_id in playlist_ids:
            if self.debug_print: 
                name = self.spot_obj.playlist(playlist_id=playlist_id)['name']

            spot_number = playlist_ids.index(playlist_id)
            if only_add_owned_playlists:
                if self.spot_dict['playlists'][spot_number]['owner']['id'] == self.spot_dict['user']['id']:
                    if self.debug_print:
                        print(f'inserting tracks from {name} in slot {spot_number}')
                    self.spot_dict['playlists'][spot_number]['tracks']['items'] = self._playlist_item_pagination(playlist_id)
                else:
                    if self.debug_print:
                        print(f'skipped {name}\n')
            else:
                self.spot_dict['playlists'][spot_number]['tracks']['items'] = self._playlist_item_pagination(playlist_id)
                if self.debug_print: 
                    print(f'inserting tracks from {name} in slot {spot_number}')
        return self.spot_dict['playlists']

    @timer
    @lru_cache
    def get_all(self):
        """a shortcut. get all the data from a profile"""
        self.get_liked_songs()
        # self.get_saved_albums()
        # self.get_top_items()
        self.get_items_from_playlists()
        return self.spot_dict

    @lru_cache
    def return_spot_dict(self):
        """gives the dict without redoing all the api calling. cached."""
        return self.spot_dict
