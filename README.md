# hobby-home-automation
A project to make a DVR, Beaglebone black and Mikrotik routerOS work together.

Not so brief Story of this project: 
Once upon a time, there was a beautiful farm, with acres of land,
a farm house for the workers and a villa for the owner.Both the farm 
house and the villa were equipped with their own DVRs and a bunch of 
cameras around them, one could say the security was important to the
owner. One day our the owner thinks that it is a good idea 
to give view access of the cameras around the villa to the labourers 
about 1Km away in their house. Of course there was a point to point 
wireless link between two places that the owner could see the cameras 
of the workers from the comfort of his villa. So he gave the job to a 
handsome professional (ehem, yours truly). Our handsome pro does the job 
and configures some things here and there and also makes the DVRs 
accessible via internet for the owner to see the cameras on his mobile
phone. After a few days the owner noticed something and said to himself,
oh nooooo! what have I done?! Me and my family have no privacy anymore!
So he does not eat anything for two days and thinks day and night. And
finally he comes up with a brilliant idea. He calls out for the
handsome pro, and asks him to place a push button near his TV set so he
can block the view access of the villa's cameras to the workers house
whenever he need some privacy. Ok this is the end of story, the hansdome
pro will take over from here, and tells you how he did it.

OK so we have two old Hikvision DVRs (DS-7208HVI-SV), a Beaglebone 
Black, a Mikrotik wireless radio. Those old DVRs support 8 analog 
cameras (with BNC and stuff) and two ip cameras, so to give access 
to all the cameras from the workers house to the villa,
we had to enable channel zero on the villas DVR and import it as one
ip camera in the workers DVR.

What I tought would be feasible, was to create a bridge filter rule on
the Mikrotik radio and somehow enable or disable it with a push of a 
button. I made a box with a push button and a red LED, to indicate
the status of the privacy. Within the filter rule I put the MAC address
of the villas DVR as destination address and configured the action to
DROP, so when it is enabled, routerOS will drop any connection destined
to it, but the connection from the villa is still possible(no video loss
from the villa).

The logic I came up with was for the beaglebone to check every few
seconds the output alarm status of the DVR (There is a seperate output
so that you can connect a siren alarm, and is a different thing than the
internal buzzer aka piezo speaker). This alarm output is just a simple
relay, so you can either attach a siren or whatever that can be turned
on/off by this relay. I have done this before, the interesting thing is
that you can trigger the alarm ouput via your mobile phone since the 
mobile app (ivms-4500) has this functionality built-in.
One way to go was to attach the ouput alarm pins to the beaglebone and
read the status of it and act on it, but when I was searching fo a way
to activate/deactivate the alarm ouput when the button is pressed I
came across this thing called ISAPI that seemingly our humble DVRs came
with. Since this is an old piece of sh... hardware and they are a 
product of china, the documentation is poor if you are lucky enough to 
find one , or are very vague and written in bad enlish. But since I am
a very lucky guy I found one and surprised that there are so many
things that I could do with it! I could read the alarm status, activate
and deactivate it! So I decided to not bother with the alarm output
relay pins, and just trigger it via API requests, I put a delay for 3
seconds, to read the status, it is not real time but it works perfectly
in this situation.
Another way to go that came to my mind at the time was to get root
shell on the poor old thing and do this with SSH maybe, or make my own
API on it, but since hardware hacking takes god knows how much time,
I scrached this idea ASAP.

Ok, back to the logic. It is a very simple code actually. Once I found
all the bolts and nuts. I did not put much time on it so it seems a bit
ugly , but I will let my ugly code speak for itself.

The first problem I faced was how to activate or deactivate the alarm,
the document said something about an html PUT method, so I dug here
and there and found out that I should send an xml payload via PUT
method, and it just took me about 4 hours to find the correct format
for it, it is provided in the same repository.

The second problem was with the <a target='_blank' href='https://pypi.org/project/RouterOS-api/'>Routeros-api</a>
, I found out that it was an old api for Mikrotik RouterOS, and was
written for python2, with python3 you get these annoying errors here
and there,  but in the github issues section I found out this cool guy
that <a target='_blank' href='https://github.com/okazdal/RouterOS-api'>forked</a> and made it usable for python3 so I removed the pip version and installed this fork instead and it works
flawlessly.

Another problem was, since the main function needed to loop
indefinitely and sleep for a few seconds, it would block the detection
of the button getting pushed. I tought about python asyncio, and
started planning the logic and coding with asyncio. But after reading
the amazing <a target='_blank' href='https://adafruit-beaglebone-io-python.readthedocs.io/en/latest/GPIO.html'>Adafruit_BBIO module documents</a>, I found out that there is an easy
solution for the problem! So there is this GPIO.add_event_detect
function that waits for an input pin event(FALLING,RISING,BOTH) with
the ability to add a callback function that runs on its own thread,
so I happily deleted the code(my baby!) I had already written and
forgot about asyncio (Ah, life is good!).

Since this script runs on beaglebone black and no one has access
to it, I didn't bother to put the credentials in a seperate file
and importing them via environment variables.
