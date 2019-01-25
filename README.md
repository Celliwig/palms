                         _..                                                 
                        sw$J%,        __.                                    
                         <WQQL   ._y29s.                                     
               .__       "w$WW  <QQ@Y^_aaawaw2;                              
           _ayQQQQQQywa,."wmQm(mQWT*wQQQQWDY"                                
         ayQ@WQWW@$WVQQQQw)$Q@QWQD(yWB}+%"'                                  
       aPWP5ZXDmhJTrAT$QQQQyQQWQP\mH$QZT??'                                  
     =TsjwmQQWQQQQQQQWWg%WWQWWP{wWH$wawmmQQQm#aa,                            
         ^ - "_?^)"")5mgWWQWWWQQW@WWWQQWQQwJ(\5]W$WWBQa )XQD_                
                   .swWWWQQQ#QQQQQDj44mWQQWQQmJ/(7QQWmWL-UQQk    ._a<~       
                 _v$WWWQDQQDJ4QQQWQ;])]jWWWQQQQQmQQWQmBQcqQW> _iwmWe~        
                auQQWWQQnQW"w$mQQQQmc -ZQ"WWWWWQQQIQQQQQQXQ5_wQQ@!~          
               ndQQQQDQQPWE)w$QQQQQQ7'.<mwmWQmmQQWQmTVQQQQ@Lm@Ymmwwgm,,      
              )mQQQm$mWD_Q["jYmWQQQW@a7YS3q#QQQQQQQWVo$QQWqW$yWQU#WBZ9QQq,,  
             )mQQQBWj]( jQ %\!yQQQQL4, -~"s3*2qWQQQQQmgdQmQQWQQQWmQWw\"76%"^.
            _ZQQQW]["   QE  `\yQQQQQ,\     amQ@QWQWQD$WQWgmmd77WTQQQQQs. -'  
           _"dQQffP    <Wf  .Z!dQQQ%[    _mQSW3P]WgQWWm54QQQQQma 5$W4QQm_    
            ]\FQ'-     ]Q[  / )jQQ3f    =@C2?`\mQWWk4Z'/hQQQmZQQQc-[ZQQQC,   
            `J`^       mQ`    <QQQ['    ~-  .wWQQ3rmP' jWQWQgSGdQQg,^j3WC    
             `         QQ     d$Q)[        _mQWFX-wP   )]QQQDC(Y@WQQ/'^f(    
                       QQ     ?dF         .mQB]`.yP    %$9mD7r  "d@QQ/       
                      :QQ      P          ]@(  .mP     )aWQQ/    ^]$$E       
                      )QQ                      yP      ^%$G!`     `]/m       
                      ]WQ.                    jQ'       .!         ``[       
                      ]WQ;                   <Q[                             
                      ]QQ[                  .mD                              
                      ]WQf                  jQ'                              
                      =QQk                 _Qf                               
                      -QQQ                 m@                                
                       QQQ/               ]Q'                                
                       WWQL              .QP                                 
                       ]QQQ.     ,       jQ'                                 
                       )WQQL    y       <QP,'                                
                        WQQQ/  jE      .QQP;                                 
                        ]WQQQ,_Qf _<,  yQQ"                                  
                         WQQWQdP_y[-m jQQW_-.s,                              
                        a)WQQQQaW6J6dmQQQWc3(                                
                     _saa#QWQQQWQQQQmmQQQmp:`                                

# P.A.L.M.S. (Pi Adagio LCD Music Streamer)

# Overview
This is a simple music streamer app designed to provide internet radio and MPD browser functionality on a standalone piece of equipment such as a hifi seperate system. This program was developed to run on a Raspberry Pi connected to the front panel of an Adagio Sound Server, however it should be easy to adapt for any system providing a 4x20 character display. While there is a command line interface implemented in ncurses, it is not recommended to run it like this. That interface is provided to make development/debugging easier, not to run the streamer full time as certain features were not designed with ncurses in mind. There are better command line tools out there, see the end.

# Features
 - Supported playback formats, see MPD.
 - SQLite backed config (includes radio station list, 8 x radio presets, etc).
 - Provides navigation of MPD music directory and basic playlist construction.
 - When run as root, drops privileges to a specified user

# User interface
All interaction with the outside world is through a ncurses like class, dev_panel.py. This communicates with a character device provided by kernel module piadagio_fp (see Celliwig/piadagio_fp). If you wish to interface with an alternate display/button board these are the two items to inspect. This was done so that the streamer app could be kept as simple as possible and leave the hard work of i2c communication to the kernel.

# See also
 - https://bobrathbone.com/raspberrypi/pi_internet_radio.html 
 Rich feature set, did consider using this instead of writing my own, but there were some design descisions which I didn't like so didn't end up trying it. However might be what you're looking for.
 - https://www.musicpd.org/clients/ncmpc/
 Excellent CLI ncurses MPD client, which proved quite handy when trying to debug my own!
