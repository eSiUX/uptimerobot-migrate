#!/usr/bin/python
# -*- coding: utf-8 -*-

import urllib, httplib, datetime, time, pprint

from logni import log

try:
        import json
        log.ni( 'use python module json', DBG=1 )

except ImportError:
        import simplejson as json
        log.ni( 'use python module simplejson as json', DBG=1 )



class UptimeRobot:

        def __init__(self, apiKey):
                """
                 * Inicializace objektu pro praci s uptimeRobot API
                 *
                 * @param apiKey        autorizacni retezec
                """

                self.__apiKey           = apiKey
                self.__apiDomain        = 'api.uptimerobot.com'



        def request( self, url='/getMonitors', paramList={} ):
                """
                 * Autorizovany request na pozadovana data
                 * ID pripadnych chyb: http://uptimerobot.com/api
                 *
                 * @param url           URL pro data
                 * @param paramList     parametry requestu
                 * @return              slovnik s navratovym stavem + daty
                """

                ret = {
                        'statusCode'    : 200,
                        'statusMessage' : 'OK'
                }

                parList = {
                        'apiKey'        : self.__apiKey,
                        'format'        : 'json',
                        'noJsonCallback': 1
                }
                parList.update(paramList)

                conUrl = "%s?%s" % (url, urllib.urlencode(parList) )

                log.ni("UptimeRobot - url: %s", (conUrl,), INFO=3)

                connection = httplib.HTTPConnection(self.__apiDomain)

                connection.request('GET', conUrl)

                response = connection.getresponse()

                status  = response.status
                data    = response.read().decode('utf-8')

                if status == 200:

                        data = json.loads(data)

                        # dotaz probehl v poradku
                        if data['stat'] == 'ok':
                                log.ni("UptimeRobot - response - status: %s, data: %s", (status, data), INFO=3)

                                ret['data'] = data
                        else:
                                log.ni("UptimeRobot - response - stat: %s, id: %s, message: %s", ( data['stat'], data['id'], data['message'] ), ERR=4)

                                ret['statusCode']       = 500
                                ret['statusMessage']    = "stat: %s, id: %s, message: %s" % ( data['stat'], data['id'], data['message'] )
                else:
                        log.ni("uptimeRobot - response - status: %s, data: %s", (status, data), ERR=4)

                        ret['statusCode']       = status
                        ret['statusMessage']    = data

                return ret
                


        def sourceOutputInfo(self, date, monitorId):
                """
                 * Namerene hodnoty pro predany zdroj
                 *
                 * @param date          datum monitorovani, ISO format
                 * @param monitorId     ID zdroje
                 * @return              slovnik s navratovym stavem + daty
                """
               
                dateEnd = datetime.datetime.strptime(date, "%Y-%m-%d") + datetime.timedelta(days=1)

                paramList = {
                        'logs'                  : 1,
                        'responseTimes'         : 1,
                        'alertContacts'         : 1,
                        'monitors'              : monitorId,
                        'responseTimesStartDate': date,
                        'responseTimesEndDate'  : dateEnd
                }

                ret = self.request('/getMonitors', paramList=paramList)

                if ret['statusCode'] != 200:
                        return ret

                data = {
                        'sender': [],
                        'output': []
                }

                contactType = {
                        '1': 'sms',
                        '2': 'email',
                        #'3': 'twitter',
                        #'4': 'boxcar',
                        #'5': 'webhook',
                        #'6': 'pushbullet',
                        #'7': 'zapier',
                        #'9': 'pushover',
                        '10': 'hipchat',
                        '11': 'slack'
                }

                monitorList = ret['data'].get( 'monitors', {} ).get( 'monitor', [] )

                if not monitorList:
                        ret['data'] = data
                        return 

                #pprint.pprint( ret['data'] )

                # odeslane zpravy o vypadku, seznam vsech poslednich logu, nemusi byt pro dane datum
                for log in monitorList[0].get( 'log', [] ):

                        checktime = datetime.datetime.strptime(log['datetime'], "%m/%d/%y %H:%M:%S")

                        if checktime.strftime('%Y-%m-%d') != date:
                                continue

                        # pro kazdy kontakt pridame odeslanou zpravu
                        for contact in log['alertcontact']:

                                data['sender'].append({
                                        'checktime'     : int( time.mktime( checktime.timetuple() ) ),
                                        'type'          : contactType.get('type', ''),
                                        'contact'       : contact.get('value', '')
                                })

                # data z mereni, je nam vracen pouze response time
                for output in monitorList[0].get( 'responsetime', [] ):
                        
                        checktime = datetime.datetime.strptime(output['datetime'], "%m/%d/%y %H:%M:%S")

                        if checktime.strftime('%Y-%m-%d') != date:
                                continue

                        # cas je uveden v ms
                        responseTime = int( output['value'] ) / 1000.0

                        # zaokrouhleni na 3 desetinna mista, pod pythonem 2.6 neni mozne pouzit round() ani format
                        responseTime = float( '%.3g' % responseTime )

                        data['output'].append({
                                'checktime'     : int( time.mktime( checktime.timetuple() ) ),
                                'responseTime'  : responseTime
                        })

                ret['data'] = data

                return ret



if __name__ == '__main__':

        log.mask( 'ALL' )
        log.stderr( 1 )

        ur = UptimeRobot('API_KEY')

        #pprint.pprint( ur.request('/getAccountDetails') )
        #pprint.pprint( ur.request('/getMonitors', paramList={'logs': 1, 'responseTimes': 1, 'alertContacts': 1, 'monitors': 776565908, 'responseTimesStartDate': '2015-05-31', 'responseTimesEndDate': '2015-06-01', 'showMonitorAlertContacts': 1} ) )

        pprint.pprint( ur.sourceOutputInfo('2015-06-01', 776565908) )
