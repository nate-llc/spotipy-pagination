import spotipy

def main(spot_dict = {}):

    #make a spotipy object however you see fit, make that equal to spot_obj
    spot_obj = spotipy.Spotify() #you need an auth token here
    
    #user info
    spot_dict['user'] = spot_obj.current_user()
    

    def multiple_api_calls(func, limit = 50):
        
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
        
        spot_dict['longer_list'] = longer_list

        #looks inside of the longer_list, yoinks the ['items'], then adds them to a combined_list
        #this means that we're only taking out the 'items' and putting them in the value of whatever dict key we're calling it from
        #meaning that we're losing all the information that's not in ['items']. if you want this, you can still save it by
        #doing something like spot_dict['key'][x] = longer_list and doing something with that info
        #if none of this makes sense to you, mess around with the raw json spotify gives you and compare that with what this function gives you
        combination_list = []      
        for iteration in longer_list:
            for x in range(len(iteration['items'])):
                combination_list.append(iteration['items'][x])
        return combination_list


    def multiple_api_calls_playlist(spot_obj, playlist_id, limit = 100):
        #this one is a little frustrating because the only difference between this and multiple_api_calls() is that i needed an extra function argument 'playlist_id'
        #which can't be present for the other functions. i think you can do something with **kwargs but i couldn't understand how
        total = spot_obj.playlist_tracks(playlist_id = playlist_id, limit = 1)['total']
        iterations = (int((total / limit)) + (total % limit > 0))
        longer_list = []
        for x in range(iterations):
            response = spot_obj.playlist_tracks(playlist_id = playlist_id, limit = limit, offset = x * limit)
            longer_list.append(response)

        combination_list = []      
        for iteration in longer_list:
            for x in range(len(iteration['items'])):
                combination_list.append(iteration['items'][x])
        return combination_list

    #grab liked_songs, and saved_albums, from user object, add them to spot_dict if truthy
    liked_songs = multiple_api_calls(func = spot_obj.current_user_saved_tracks, limit = 50)
    if liked_songs: 
        spot_dict['liked_songs'] = liked_songs
    
    saved_albums = multiple_api_calls(func = spot_obj.current_user_saved_albums, limit = 50)
    if len(saved_albums):
        spot_dict['saved_albums'] = saved_albums
    
    
    #this gives you everything about the playlist except for the tracks within it
    playlists = multiple_api_calls(func = spot_obj.current_user_playlists, limit = 50)
    if playlists:
        #put the spotify return inside of our dict, it's a tool we're going to use for later
        spot_dict['playlists'] = playlists

        def list_playlist_ids(spot_dict):
            #this makes a list of all the playlist_ids, purely just so we can iterate over them easier in just a second
            ids = []
            for x in range(len(playlists)):
                ids.append(spot_dict['playlists'][x]['id'])
            spot_dict['playlist_ids'] = ids

        def insert_playlist_items(spot_dict, only_add_owned_playlists):
            #take that list of playlist_ids, insert that id in multiple_api_calls_playlist(spot_obj, id)
            #we need the spot_number because in ['playlists'], it's ordered from 0 up. this is the spot in which we're going to put the tracks
            for id in spot_dict['playlist_ids']:
                spot_number = spot_dict['playlist_ids'].index(id)
                name = spot_dict['playlists'][spot_number]['name']
                
                #this is just in case you don't want a ton of non-owned, but saved, playlists in your dictionary. 
                #this function can take quite a minute depending on how many playlists and how big they are
                #we're putting the tracks in ['tracks']['tracks'] because there's already some data in ['tracks'] and i figure it will be easier to iterate over in the future
                if only_add_owned_playlists:
                    if spot_dict['playlists'][spot_number]['owner']['id'] == spot_dict['user']['id']:
                        spot_dict['playlists'][spot_number]['tracks']['tracks'] = multiple_api_calls_playlist(spot_obj, id)
                        print(f'added {name}')
                    else:
                        print(f'skipped {name}')
                else:
                    spot_dict['playlists'][spot_number]['tracks']['tracks'] = multiple_api_calls_playlist(spot_obj, id)
                    print(f'added {name}')

        #calling the two functions because i think it makes variable-lookup stuff more performant and also it's easier to temporarily disable for debugging purposes
        list_playlist_ids(spot_dict)
        insert_playlist_items(spot_dict, True)

    return spot_dict 


