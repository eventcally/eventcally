from flask_babelex import lazy_gettext

event_rating_choices = [
            (0,lazy_gettext('0 (Little relevant)')),
            (10,'1'),
            (20,'2'),
            (30,'3'),
            (40,'4'),
            (50,'5'),
            (60,'6'),
            (70,'7'),
            (80,'8'),
            (90,'9'),
            (100,lazy_gettext('10 (Highlight)'))
        ]
