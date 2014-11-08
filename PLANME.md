# System Components

- Message Queue
- OpenNI Device Monitor
- Dance Interpreter
- MusicCoord Decision Engine
- Music Player
- *[UPDATE THIS]* Suite de Visualization
- *[UPDATE THIS]* ...

# Messaging

Messaging is done with [Redis PUB/SUB](http://redis.io/topics/pubsub). Message contents are [JSON](http://www.json.org/) strings.

## Message Types

Different message types will be sent on different redis pub/sub channels.

*Exact formats TBD*

### `dancer-state`

These messages will stream rapid fire.

    {
        "timestamp": 1415489686,            // when this update came in, long - time in milliseconds
        "points": {
            "head": [1,1,1],                        // Head position X,Y,Z
            "neck": [1,2,1],                        // Neck position x,y,z
            ...                             // the other ones too... full list soon
        }
    }

### `dance-beat`

These messages will spew out as irregularly as Tanner dances.

    {
        "timestamp": 1415489686,            // when we noticed this beat, long - time in milliseconds
        "type": "head",                     // what part of the body that is rocking a beat
        "position": [1,1,1],                // where was the head when this went down
        "intensity": 123                    // how intense was that head bob
    }

*intensity scale to be decided*

### `dance-move`

These messages will happen rarely and are saved for special occasions.

    {
        "timestamp": 1415489686,            // when we noticed this stance, long - time in millis
        "move": "boogie-nights",            // what move did we notice
        "intensity": 1234234                // how epic was this move's execution
    }

#### Moves we can notice *...probably*

- boogie-nights
- metal-headbang
- drunk-and-passed-out
