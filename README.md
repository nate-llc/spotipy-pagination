# spotipy-multiple-api-requests
this gets around the 50 track/album/playlist and the 100 playlist track limitation of spotify's api using spotipy

the notes in the code explain how this is happening
grab your spotipy user object, throw it in the script, and you'll get a reasonably legible dictionary
.
i tried to use more basic for loops and whatnot to get multiple lists of, for example, saved tracks but parsing through it was a nightmare
and was influenced by the interpretation of json

you'll notice that there's not actually any json objects in this script, just one big python dictionary
this is probably not very good for performance, but i was trying to understand how to use json 'the right way' and it just didn't work out the way i thought it would

so here it is, a really, really big dictionary with different bits of spotify user data
there's no reason why you coudln't add on top of this, i looked at spotipy's api doc and i couldn't really find other information that i really wanted or cared about

but if it's the case that the function you want to use just has a limit and an offset, throw it in multiple_api_calls() and it should work just fine

feel free to dm me about questions, i'm really happy with how this turned out for my first intermediate script that seems to be somewhat useful (i couldn't find anything online about this which i found really strange)

edit: 2 November 2022

I realize now that this problem has been solved by people smarter than I am, including in the examples folder of the spotipy github. This was not apparent to me when I made this, and even now I'm glad to have done it. I learned a lot about JSON and the Spotify API, and the Spotipy people made a really good thing with it. However, it's not async which isn't the best. Some day I'll get around to learning Spotipy2, which I would love to do if there were any documentation for it. I would love to contribute such documentation, but I genuinely don't know how it works and it's pretty advanced stuff. I'll see what I can do after my song-sorter project.

Anyways, my class is a pretty good tool for paginating through the Spotify API with nothing but the auth code. If you have any questions about it, feel free to shoot me a dm or whatever github people do