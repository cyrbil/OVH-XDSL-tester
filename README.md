# OVH XDSL Tester

This script will test all profiles from OVH'S XDSL offers, and launch a speedtest for each.
Once done you will be able to see which profile is the best for you.

> Warning: The test is long and make you lose connection, pick a moment when you have 2 hours free.
You can reduce the number of profiles by editing the script and manually filter. Also, some profile
might not work on your connection, resulting in a lose of internet and this script stuck. Prepare
a backup networking solution in this case, to switch back to a working profile.

## Usage

Simply execute the script with python, and follow the steps.
It will install dependencies and handle OVH's API authentication.
If you have many xdsl accounts or  lines, a prompt will ask to pick the one to test.

    $ python tester.py
    Authentication needed, please go to: https://eu.api.ovh.com/auth/?credentialToken=token
    login and then press enter to continue...

    This will test out every configuration for xdsl-xxxxxxx-1 - 0412345678
    It will take a long time and your connection will be unstable during the test
    Press enter when ready ...

    Starting ...
    Found 4 profiles, testing will take nearly 8 minutes
    Tests will be done against server: bayonne.iperf.fr
    DURATION                          PROFIL    PING      DOWNLOAD        UPLOAD
         70s        VDSL 17a TURBO SNR3 FAST    19ms    31.23 Mbps     3.73 Mbps
        125s        VDSL 17a TURBO SNR1 FAST    19ms    32.40 Mbps     8.17 Mbps
        117s  G.INP VDSL 17a TURBO SNR3 FAST    19ms    31.83 Mbps     7.32 Mbps
        119s  G.INP VDSL 17a TURBO SNR1 FAST    20ms    32.19 Mbps     7.54 Mbps

    Applying best found profile "VDSL 17a TURBO SNR1 FAST"
    All done !



