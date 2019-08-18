#################################################################################################
#################################################################################################
# ---------------------------- Spotify Sub-Playlist And Sort --------------------------------- #
#  This script takes a playlist, which happens to be too long for the occasion, orders it by a  #
#  chosen audio feature (e.g. 'danceability, 'energy', 'tempo') and then randomly selects songs #
#  across the range of the selected audio feature.                                               #
#################################################################################################
#################################################################################################
#  Import some Libraries
import pandas as pd
import spotipy
import spotipy.util as util
import sys
import time
import datetime
import math
import matplotlib.pyplot as plt

# pandas settings for visulasing results if needed
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

#  Enter variables
playlistName = 'PlaylisName'
username = 'YouUserName'
newPlName = 'NewPlaylistName'
desired_dur = 120 # Playlist length in minutes
sortby = 'energy' # audio attribute see: https://developer.spotify.com/documentation/web-api/reference/tracks/get-audio-features/

def Credentials():

    token = util.prompt_for_user_token(
        username = username,
        scope='playlist-modify-private playlist-modify-public',
        client_id='...client.id...',
        client_secret='...client.secret...',
        redirect_uri='http://localhost/')

    if token:
        sptok = spotipy.Spotify(auth=token)
        return sptok
    else:
        print("Can't get token for", username)
        sys.exit()


def ProcPlaylist(sp):

    PL_list = []

    playlists = sp.user_playlists(username)
    for playlist in playlists['items']:

        PL_list.append(playlist['name'])
        if playlist['name'] == newPlName:
            print("\nPlaylist with name {0} already exists \n"
                  "Select a new name!!!!".format(newPlName))
            sys.exit()

        if playlist['name'] == playlistName:
            if playlist['owner']['id'] == username:
                print()
                print(playlist['name'])
                print('  total tracks', playlist['tracks']['total'])
                results = sp.user_playlist(username, playlist['id'],
                                           fields="tracks,next")
                tracks = results['tracks']
                show_tracks(tracks)

                tidl = get_playlist_tracks(username, playlist['id'])

    tracklist = []
    for i in tidl:
        tracklist.append(i['track']['external_urls'].get('spotify'))

    track_stats = []

    for i in tracklist:
        audFeat = sp.audio_features([i])
        audFeatDf = pd.DataFrame(audFeat)
        track_stats.append(audFeatDf)

    af_df = pd.concat(track_stats)

    af_df = af_df.reset_index(drop=True)
    # print(af_df)


    sorted_df = af_df.sort_values([sortby])
    sorted_df = sorted_df.reset_index(drop=True)

    # print(sorted_df)

    pl_tot_time = sum(sorted_df['duration_ms'])
    pl_avg_time = sum(sorted_df['duration_ms'])/len(sorted_df)
    print("playlist length = {0}".format(str(datetime.timedelta(seconds=pl_tot_time / 1000))))
    print("average track length = {0}".format(str(datetime.timedelta(seconds=pl_avg_time / 1000))))

    n_songs_ap = math.ceil((desired_dur*60000)/pl_avg_time)

    chunk_size = math.floor(len(sorted_df)/n_songs_ap)

    tracksToAdd = []
    s1 = 0
    for i in range(1, n_songs_ap+1):
        # print(i)
        s1 += chunk_size
        if i == 1:
            temp_df = sorted_df[:chunk_size]
        elif i == n_songs_ap:
            temp_df = sorted_df[s1:]
        else:
            temp_df = sorted_df[s1-1:(s1+chunk_size)]
        try:
            chosen_track = temp_df.sample()
            trackID = chosen_track.iloc[0]['uri']
            tracksToAdd.append(trackID)
            print('{0}         {1}'.format(chosen_track.iloc[0]['uri'], chosen_track.iloc[0][sortby]))
        except ValueError as e:
            print(e)
    print(len(tracksToAdd))


    new_pl = sp.user_playlist_create(username, newPlName, public=True)
    pl_owner_id = new_pl['owner'].get('id')
    pl_id = new_pl['id']

    for t in tracksToAdd:
        # print(t)
        sp.user_playlist_add_tracks(username, pl_id, [t])
        time.sleep(0.5)
    sp.user_playlist_follow_playlist(pl_owner_id, pl_id)

    sorted_df.hist(column=sortby)
    plt.show()
    print("playlist completed...")


def get_track_stats(username,playlist_id):
    results = sp.user_playlist_tracks(username,playlist_id)
    tracks = results['items']
    while results['next']:
        results = sp.next(results)
        tracks.extend(results['items'])
    return tracks

def get_playlist_tracks(username,playlist_id):
    results = sp.user_playlist_tracks(username,playlist_id)
    tracks = results['items']
    while results['next']:
        results = sp.next(results)
        tracks.extend(results['items'])
    return tracks


def show_tracks(tracks):
    for i, item in enumerate(tracks['items']):
        track = item['track']
        print ("   %d %32.32s %s" % (i, track['artists'][0]['name'],
            track['name']))


if __name__ == '__main__':
    sp = Credentials()
    ProcPlaylist(sp)

