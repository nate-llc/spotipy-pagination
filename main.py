import spotipy
import time
from timer import timer

#use this class by making an object
#object = SpotDict(spotipy_authorization_token)
#then use the methods as available, 
#object.get_liked_songs() - get all of a user's liked songs
#object.get_saved_albums() - get user's saved_albums and the tracks inside
#object.get_playlsits() - gets all the data about the playlist except for the tracks inside
#object.get_playlists_and_items() - this one takes the playlists and adds the tracks inside of those playlists inside of ['tracks'] | can be very performance/data heavy with very large playlists, consider making a maximum limit or something

class SpotDict:

    def __init__(self, auth):
        self.spot_obj = spotipy.Spotify(auth) #you need an authetication token here, see spotify/spotipy docs
        self.LIMIT_ITERATIONS = False #for debugging, only go through the different iterations in multiple_api_calls() a certain number of times.
        self.SLEEP_TIME = 0 #sleep time for api-call budgeting
        self.REMOVE_AVAILABLE_MARKETS = True #available markets is a lot of data to store (over half of the text data!) so this removes all of that
        self.MAX_PLAYLIST_CALCULATION = False #for debugging, if you only want to calculate a few playlists instead of all of them.
        self.spot_dict = {}
        self.spot_dict['user'] = self.spot_obj.current_user()


    def remove_available_markets(self, iteration, func, x):
        try:
            iteration['items'][x]['track'].pop('available_markets')
            iteration['items'][x]['track']['album'].pop('available_markets')
            if "available_markets" not in iteration['items'][x]['track'].keys():
                print(f"successfully removed available_markets from {str(func)}")
            
        except:
            try:
                iteration['items'][x]['album'].pop('available_markets')
                print(f'removed available_markets from album {iteration["items"][x]["album"]["name"]}')
                for song in iteration['items'][x]['album']['tracks']['items']:
                    song.pop("available_markets")
                print(f'removed available_markets from songs inside album {iteration["items"][x]["album"]["name"]}')
            except:
                if 'Spotify.current_user_playlists' not in str(func):
                    print(f"couldn't remove available_markets from {str(func)}")
        return iteration

    @timer
    def multiple_api_calls(self, func, limit = 50):

        if self.LIMIT_ITERATIONS:
            iterations = self.LIMIT_ITERATIONS
            limit = self.LIMIT_ITERATIONS
        
        #func is a variable because this exact method works for multiple information requests from spotify.
        #they have a consistent scheme that the JSON follows. 
        #limit = 50 because that's the max for these functions.

        #get how many api requests we need, round up
        total = func(limit=1)['total']
        iterations = (int((total / limit)) + (total % limit > 0))

        longer_list = []
        
        for x in range(iterations):
            #actaully grab the information from func().
            #example = spot_obj.current_user_saved_tracks(limit = limit, offset = x * limit)
            #take those different api pulls and put them in longer_list 
            response = func(limit=limit, offset= x * limit)
            longer_list.append(response)
        
        #looks inside of the longer_list, yoinks the ['items'], then adds them to a combined_list
        #this means that we're only taking out the 'items' and putting them in the value of whatever dict key we're calling it from
        #meaning that we're losing all the information that's not in ['items']. if you want this, you can still save it by
        #doing something like spot_dict['key'][x] = longer_list and doing something with that info
        #if none of this makes sense to you, mess around with the raw json spotify gives you and compare that with what this function gives you
        combination_list = []      
        for iteration in longer_list:
            for x in range(len(iteration['items'])):
                if self.REMOVE_AVAILABLE_MARKETS: self.remove_available_markets(iteration, func, x)
                combination_list.append(iteration['items'][x])
        return combination_list
    
    @timer
    def get_liked_songs(self):
        liked_songs = self.multiple_api_calls(func = self.spot_obj.current_user_saved_tracks, limit = 50)
        if liked_songs: 
            self.spot_dict['liked_songs'] = liked_songs
            print('added liked songs to dict')
    
    @timer
    def get_saved_albums(self):
        saved_albums = self.multiple_api_calls(func = self.spot_obj.current_user_saved_albums, limit = 50)
        if len(saved_albums):
            self.spot_dict['saved_albums'] = saved_albums
            print('added saved albums to dict')
    
    @timer
    def get_top_items(self):
        top_items = self.multiple_api_calls(func = self.spot_obj.current_user_top_tracks, limit = 50)
        if top_items:
            self.spot_dict['top items'] = top_items
            if self.DEBUG_PRINT: print(f'added {len(top_items)} top items to dict')

    @timer
    def multiple_api_calls_playlist(self, playlist_id, name, limit = 100):
        #this one is a little frustrating because the only difference between this and multiple_api_calls() is that i needed an extra function argument 'playlist_id'
        #which can't be present for the other functions. i think you can do something with **kwargs but i couldn't understand how
        total = self.spot_obj.playlist_tracks(playlist_id = playlist_id, limit = 1)['total']
        iterations = (int((total / limit)) + (total % limit > 0))
        if self.LIMIT_ITERATIONS:
            iterations = self.LIMIT_ITERATIONS
            limit = self.LIMIT_ITERATIONS
        longer_list = []
        song_number = 0
        for x in range(iterations):
            response = self.spot_obj.playlist_tracks(playlist_id = playlist_id, limit = limit, offset = x * limit)
            longer_list.append(response)
            
            print(f'added songs {song_number} through {song_number + limit}')
            print(f'waiting {self.SLEEP_TIME} seconds')
            song_number += limit
            time.sleep(self.SLEEP_TIME)
        combination_list = []      
        for iteration in longer_list:
            for x in range(len(iteration['items'])):
                if self.REMOVE_AVAILABLE_MARKETS:
                    iteration['items'][x]['track'].pop('available_markets')
                    iteration['items'][x]['track']['album'].pop('available_markets')
                combination_list.append(iteration['items'][x])
        print(f"added {len(combination_list)} songs from playlist {name} with playist id {playlist_id} to dict")
        return combination_list

    @timer
    def get_playlists(self):
        self.playlists = self.multiple_api_calls(func = self.spot_obj.current_user_playlists)
        self.spot_dict['playlists'] = self.playlists
        print(f'added {len(self.playlists)} playlists to dict')

    @timer
    def get_playlists_and_items(self, only_add_owned_playlists = True): 
        #this makes a list of all the playlist_ids, purely just so we can iterate over them easier in just a second
        #this is inside its own sub-function for @timer logging
        @timer
        def playlist_ids(self):
            ids = []
            for x in range(len(self.playlists)):
                ids.append(self.spot_dict['playlists'][x]['id'])
            self.spot_dict['playlist_ids'] = ids
            print(f'added playlist ids to dict')
        
        playlist_ids(self)
        #take that list of playlist_ids, insert that id in multiple_api_calls_playlist(spot_obj, id)
        #we need the spot_number because in ['playlists'], it's ordered from 0 up. this is the spot in which we're going to put the tracks
        for id in self.spot_dict['playlist_ids']:
            
            if self.MAX_PLAYLIST_CALCULATION:
                if (self.spot_dict['playlist_ids'].index(id) - 1) >= self.MAX_PLAYLIST_CALCULATION:
                    break
            

            spot_number = self.spot_dict['playlist_ids'].index(id)
            #name purely for logging
            name = self.spot_dict['playlists'][spot_number]['name']
            #this is just in case you don't want a ton of non-owned, but saved, playlists in your dictionary. 
            #this function can take quite a minute depending on how many playlists and how big they are
            if only_add_owned_playlists:
                if self.spot_dict['playlists'][spot_number]['owner']['id'] == self.spot_dict['user']['id']:
                    print(f'inserting tracks from {name} in slot {spot_number}')    
                    self.spot_dict['playlists'][spot_number]['tracks']['tracks'] = self.multiple_api_calls_playlist(playlist_id = id, name = name)
                else:
                    print(f'skipped {name}\n')
            else:
                self.spot_dict['playlists'][spot_number]['tracks']['tracks'] = self.multiple_api_calls_playlist(playlist_id = id, name = name)
                print(f'inserting tracks from {name} in slot {spot_number}')
