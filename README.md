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

This is a (relatively) simple music streamer app designed to provide internet
radio, MPD browser functionality, and USB playback on a standalone piece of 
equipment such as a hifi seperate system.

This program was developed to run on a Raspberry Pi connected to the front
panel of an Adagio Sound Server. However it can easily be adapted to any 
system providing a 4x20 character display, with button controls. The expected
controls are:

	* Menu
	* Up, Down, Left, Right, Select, and Back
	* Play, Pause, Stop, Previous, and Next
	* Display select 1 thru 4

The device is controlled through a character device provided by the 
piadagio_fp module, this handles all the i2c interfacing leaving the app to
deal with the job of providing an interface to the MPD player.
