# -*- coding: utf-8 -*-
from django.test import TestCase, Client
from Sbike import views
from django.contrib.auth.models import User
from .models import Client as OurClient, Admin, Employee, Station, Bike
import os, re

# Create your tests here.

APP_NAME = 'Sbike'

class Accesos(TestCase):

    formValid = {
        'username': 'pepeloco',
        'password1': 'pepeelmascapo',
        'password2': 'pepeelmascapo',
        'first_name': 'Pepe',
        'last_name': 'Loco',
        'email': 'pepe@loco.com',
        'phone_number': '3511234567',
        'dni': '0303456',
        'card_number': '938765451673',
        'expiration_date': '2015-05-30',
        'security_code': '642'
    }

    templates = {
        'home': 'home.html',
        'register': 'client_register.html',
        'weblogin': 'web_login.html',
        'stationlogin': 'station_login.html',
        'clientprofile': 'client_profile.html',
        'emplprofile': 'employee_profile.html',
        'admprofile': 'admin_profile.html',
        'stationprofile': 'station_profile.html',
        'stations': 'stations.html',
        'bikeloan': 'bike_loan.html',
        'giveback': 'give_back.html',
        'editpass': 'client_edit.html',
        'creatst': 'create_station.html'
    }

    def test_home(self):
        c = Client()
        res = c.get('/')

        # deberia devolver la home page
        self.assertTrue(self.is_template(res, self.templates['home']))

    def test_obtener_registro(self):
        """ Intentamos obtener el formulario de registro """
        # creamos un cliente
        c = Client()
        # follow es para seguir los redireccionamientos
        res = c.get('/register', follow=True)

        # deberia devolver la register page
        self.assertTrue(self.is_template(res, self.templates['register']))

    def test_register_user(self):
        """ Intentamos registrarnos """
        c = Client()
        # Creamos un formulario invalido y lo intentamos enviar

        form = {
            'username' : 'a'
        }
        res = c.post('/register/', form, follow=True)

        # deberiamos obtener otra vez la pagina de registro
        self.assertTrue(self.is_template(res, self.templates['register']))
        
        # Ahora cramos un formulario valido
        res = c.post('/register/', self.formValid, follow=True)

        # deberiamos obtener el login
        self.assertTrue(self.is_template(res, self.templates['weblogin']))

        # y recibir el msj de exito
        try:
            res.content.index('You Have Successfully Registered')
        except ValueError:
            self.fail('Mensaje de exito no encontrado')

    def test_weblogin(self):
        """ Intentamos loguearnos (in)validamente """

        c = Client()

        # Intentamos obtener la pagina de login
        res = c.get('/weblogin', follow=True)
        self.assertTrue(self.is_template(res, self.templates['weblogin']))

        # Nos intentamos loguear con un usuario inexistente
        res = c.post('/weblogin/', {'username': 'probablementeningunusuarioexistaconestenombre',
                                    'password': 'miranda'}, follow=True)

        # Nos deberia volver a llevar al login
        self.assertTrue(self.is_template(res, self.templates['weblogin']))

        # Con un mensaje de error
        try:
            res.content.index('Invalid username')
        except ValueError:
            self.fail('Mensaje de error no encontrado')


        # ahora nos registramos 
        res = c.post('/register/', self.formValid, follow=True)        

        # deberiamos obtener el weblogin
        self.assertTrue(self.is_template(res, self.templates['weblogin']))

        # y recibir el msj de exito
        try:
            res.content.index('You Have Successfully Registered')
        except ValueError:
            self.fail('Mensaje de exito no encontrado')

        # y ahora intentamos loguearnos bien
        res = c.post('/weblogin/',
                     {'username': self.formValid['username'],
                      'password': self.formValid['password1']},
                     follow=True)

        # deberia llevarnos al perfil nuestro
        self.assertTrue(self.is_template(res, self.templates['clientprofile']))

        # revisemos que nuestro username este en el perfil
        try:
            res.content.index(self.formValid['username'])
        except ValueError:
            self.fail('Mi username no estaba en mi perfil')

        # y si tratamos de ir a la pagina de login (ya logueados)
        res = c.get('/weblogin', follow=True)

        # deberia llevarnos al perfil nuestro
        self.assertTrue(self.is_template(res, self.templates['clientprofile']))

        # revisemos que nuestro username este en el perfil
        try:
            res.content.index(self.formValid['username'])
        except ValueError:
            self.fail('Mi username no estaba en mi perfil')


    def test_stationlogin(self):
        """ intento de inicio de sesion en la estacion """

        c = Client()

        # Creamos una estacion
        self.createStation('San Martin', self.createEmployee('carlos123', 'carlitos'))

        # Intentamos obtener la pagina de login
        res = c.get('/stationlogin', follow=True)
        self.assertTrue(self.is_template(res, self.templates['stationlogin']))

        # Nos intentamos loguear con un usuario inexistente
        res = c.post('/stationlogin/', {'username': 'probablementeningunusuarioexistaconestenombre', 'password': 'miranda'}, follow=True)

        # No deberia dejarnos pasar
        self.assertTrue(self.is_template(res, self.templates['stationlogin']))

        # ahora nos registramos 
        res = c.post('/register/', self.formValid, follow=True)

        # y ahora intentamos loguearnos bien
        res = c.post('/stationlogin/',
                     {'username': self.formValid['username'],
                      'password': self.formValid['password1']},
                     follow=True)

        # deberia llevarnos al perfil de la estacion
        self.assertTrue(self.is_template(res, self.templates['stationprofile']))


    def test_view_stations(self):
        """ Intento de ver estaciones con y sin autenticacion """

        c = Client()

        # intentemos ver las estaciones sin login
        res = c.get('/stations', follow=True)

        # deberiamos terminar en el weblogin
        self.assertTrue(self.is_template(res, self.templates['weblogin']))

        # nos registramos y logueamos
        res = c.post('/register/', self.formValid, follow=True)
        res = c.post('/weblogin/',
                     {'username': self.formValid['username'],
                      'password': self.formValid['password1']},
                     follow=True)

        # ahora re-intentamos
        res = c.get('/stations', follow=True)

        # deberiamos terminar en stations
        self.assertTrue(self.is_template(res, self.templates['stations']))

    def test_logout(self):
        """ Inicio y cierre de sesion """

        c = Client()

        # Creamos una estacion
        self.createStation('San Martin', self.createEmployee('carlos123', 'carlitos'))

        # nos registramos
        res = c.post('/register/', self.formValid, follow=True)

        # nos logueamos en la estacion
        res = c.post('/stationlogin/',
                     {'username': self.formValid['username'],
                      'password': self.formValid['password1']},
                     follow=True)

        # si salio bien estamos en el station profile
        self.assertTrue(self.is_template(res, self.templates['stationprofile']))

        # cerramos sesion
        res = c.get('/logout', follow=True)

        # deberiamos terminar en la pagina de station login
        self.assertTrue(self.is_template(res, self.templates['stationlogin']))

        # nos logueamos en weblogin
        res = c.post('/weblogin/',
                     {'username': self.formValid['username'],
                      'password': self.formValid['password1']},
                     follow=True)

        # si salio bien estamos en el web profile
        self.assertTrue(self.is_template(res, self.templates['clientprofile']))

        # cerramos sesion
        res = c.get('/logout', follow=True)

        # deberiamos terminar en la pagina de web login
        self.assertTrue(self.is_template(res, self.templates['weblogin']))


    def test_webprofile(self):
        c = Client()

        # intentamos obtener webprofile sin login
        res = c.get('/webprofile', follow=True)

        # deberiamos terminar en la pagina de web login
        self.assertTrue(self.is_template(res, self.templates['weblogin']))

        # nos registramos
        res = c.post('/register/', self.formValid, follow=True)

        # nos logueamos y vamos a webprofile
        res = c.post('/weblogin/',
                     {'username': self.formValid['username'],
                      'password': self.formValid['password1']},
                     follow=True)
        res = c.get('/webprofile', follow=True)
        
        # deberiamos terminar en la pagina de client profile
        self.assertTrue(self.is_template(res, self.templates['clientprofile']))

        # cerramos sesion
        res = c.get('/logout', follow=True)

        # Ahora como empleado
        self.createEmployee('amigo123', 'empanada')
        res = c.post('/weblogin/',
                     {'username': 'amigo123',
                      'password': 'empanada'},
                     follow=True)

        # deberiamos terminar en la pagina de employee profile
        self.assertTrue(self.is_template(res, self.templates['emplprofile']))

        # cerramos sesion
        res = c.get('/logout', follow=True)

        # Ahora como admin
        self.createAdmin('eladmin', 'bariloche')
        res = c.post('/weblogin/',
                     {'username': 'eladmin',
                      'password': 'bariloche'},
                     follow=True)

        # deberiamos terminar en la pagina de admin profile
        self.assertTrue(self.is_template(res, self.templates['admprofile']))

    def test_bike_loan(self):

        c = Client()

        # crear estacion
        stat = self.createStation('San Martin', self.createEmployee('carlos123', 'carlitos'))
        # agregarle unas bicicletas
        self.addBicycles(stat, 5)

        # intentamos obtener la pagina de prestamos sin login
        res = c.get('/bikeloan', follow=True)

        # deberiamos obtener el weblogin
        self.assertTrue(self.is_template(res, self.templates['weblogin']))

        # registrarse, loguearse por weblogin
        res = c.post('/register/', self.formValid, follow=True)

        res = c.post('/weblogin/',
                     {'username': self.formValid['username'],
                      'password': self.formValid['password1']},
                     follow=True)

        # intentemos obtener pagina de prestamos
        res = c.get('/bikeloan', follow=True)

        # deberiamos terminar en clientprofile (porque iniciamos en weblogin)
        self.assertTrue(self.is_template(res, self.templates['clientprofile']))

        # ahora iniciemos en stationlogin
        res = c.post('/stationlogin/',
                     {'username': self.formValid['username'],
                      'password': self.formValid['password1']},
                     follow=True)


        self.assertTrue(self.is_template(res, self.templates['stationprofile']))

        # intentemos otra vez
        res = c.get('/bikeloan', follow=True)

        # deberiamos terminar en bikeloan
        self.assertTrue(self.is_template(res, self.templates['bikeloan']))

        # veamos que bicis tenemos para pedir
        options = find_between(res.content, '<select name="select" class="form-control" form="bikesform">', '</select>')
        if not options:
            self.fail('no tengo bicicletas para pedir')


        # pedimos la primera
        try:
            my_option = find_between(res.content, '<option value=', '>')
            my_option = int(my_option)
            my_option = str(my_option)
        except:
            self.fail('no tengo bici para pedir')

        res = c.post('/bikeloan/', {'select': my_option}, follow=True)

        # nos deberia llevar a stationprofile
        self.assertTrue(self.is_template(res, self.templates['stationprofile']))

        # con un msj de que el prestamo se ejecuto correctamente
        try:
            res.content.index('Loan: Bike '+my_option)
        except ValueError:
            self.fail('Mensaje de prestamo no encontrado')

    def test_give_back(self):
        c = Client()

        # crear estacion
        stat = self.createStation('San Martin', self.createEmployee('carlos123', 'carlitos'))
        # agregarle unas bicicletas
        self.addBicycles(stat, 5)

        # intentamos obtener la pagina de devolucion sin login
        res = c.get('/giveback', follow=True)

        # deberiamos obtener el weblogin
        self.assertTrue(self.is_template(res, self.templates['weblogin']))

        # registrarse, loguearse por weblogin
        res = c.post('/register/', self.formValid, follow=True)

        res = c.post('/weblogin/',
                     {'username': self.formValid['username'],
                      'password': self.formValid['password1']},
                     follow=True)

        # intentemos obtener pagina de devolucion
        res = c.get('/giveback', follow=True)

        # deberiamos terminar en clientprofile (porque iniciamos en weblogin)
        self.assertTrue(self.is_template(res, self.templates['clientprofile']))

        # ahora iniciemos en stationlogin
        res = c.post('/stationlogin/',
                     {'username': self.formValid['username'],
                      'password': self.formValid['password1']},
                     follow=True)


        self.assertTrue(self.is_template(res, self.templates['stationprofile']))

        # intentemos otra vez
        res = c.get('/giveback', follow=True)

        # deberiamos terminar en giveback
        self.assertTrue(self.is_template(res, self.templates['giveback']))

        # cual es la bici que tengo para devolver
        # ..................................................

    def test_edit_passw(self):

        c = Client()

       # intentamos obtener la pagina sin login
        res = c.get('/editpassword', follow=True)

        # deberiamos obtener el weblogin
        self.assertTrue(self.is_template(res, self.templates['weblogin']))

        # registrarse, loguearse por weblogin
        res = c.post('/register/', self.formValid, follow=True)

        res = c.post('/weblogin/',
                     {'username': self.formValid['username'],
                      'password': self.formValid['password1']},
                     follow=True)

        # intentemos obtener la pagina
        res = c.get('/editpassword', follow=True)

        # deberiamos terminar en editpass
        self.assertTrue(self.is_template(res, self.templates['editpass']))

        # llenar el formulario
        res = c.post('/editpassword/',
                     {'password1': 'lanuevapass',
                      'password2': 'lanuevapass'},
                     follow=True)

        # deberiamos terminar en weblogin con un msj
        self.assertTrue(self.is_template(res, self.templates['weblogin']))
        try:
            res.content.index('Password Changed Successfully')
        except ValueError:
            self.fail('Mensaje de cambio de contraseña no encontrado')

        # intentar iniciar sesion con la clave anterior deberia dar error
        res = c.post('/weblogin/',
                     {'username': self.formValid['username'],
                      'password': self.formValid['password1']},
                     follow=True)

        self.assertTrue(self.is_template(res, self.templates['weblogin']))
        try:
            res.content.index('Invalid username')
        except ValueError:
            self.fail('Mensaje de error no encontrado')

        # pero iniciar con la clave nueva nos deja en nuestro perfil
        res = c.post('/weblogin/',
                     {'username': self.formValid['username'],
                      'password': 'lanuevapass'},
                     follow=True)

        self.assertTrue(self.is_template(res, self.templates['clientprofile']))


    def test_create_station(self):

        c = Client()

       # intentamos obtener la pagina sin login
        res = c.get('/createstation', follow=True)

        # deberiamos obtener el weblogin
        self.assertTrue(self.is_template(res, self.templates['weblogin']))

        # registrarse, loguearse por weblogin
        res = c.post('/register/', self.formValid, follow=True)

        res = c.post('/weblogin/',
                     {'username': self.formValid['username'],
                      'password': self.formValid['password1']},
                     follow=True)

        # intentemos obtener la pagina
        res = c.get('/createstation', follow=True)

        # no nos deberia dejar entrar (solo para admins)
        self.assertTrue(self.is_template(res, self.templates['clientprofile']))
        try:
            res.content.index('Unavailable')
        except ValueError:
            self.fail('Mensaje de no admision no encontrado')

        # cerramos sesion
        res = c.get('/logout', follow=True)

        # ahora como admin
        self.createAdmin('lucasandy', 'iamanadmin')
        res = c.post('/weblogin/',
                     {'username': 'lucasandy',
                      'password': 'iamanadmin'},
                     follow=True)
        self.assertTrue(self.is_template(res, self.templates['admprofile']))

        # intentemos obtener la pagina
        res = c.get('/createstation', follow=True)

        # nos deberia dejar entrar
        self.assertTrue(self.is_template(res, self.templates['creatst']))

        # creamos la estacion
        res = c.post('/createstation/',
                     {'name': 'Los Platanos',
                      'address': 'Belgrano 433',
                      'capacity': 10},
                     follow=True)

        # cerramos sesion
        res = c.get('/logout', follow=True)

        # y veamos que se puede loguear desde station
        res = c.post('/stationlogin/',
                     {'username': self.formValid['username'],
                      'password': self.formValid['password1']},
                     follow=True)

        # si salio bien estamos en el station profile
        self.assertTrue(self.is_template(res, self.templates['stationprofile']))


    def addBicycles(self, station, num):
        for i in range(0,num):
            bk = Bike()
            bk.state = 'AV'
            bk.station = station
            bk.save()

    def createStation(self, name, empl, capacity=10):

        station = Station()
        station.employee =  empl
        station.create_station(name, name+ '  123', capacity)

        return station

    def createEmployee(self, username, passw):

        user = User.objects.create_user(username, '', passw)

        user.first_name = 'Carlos'
        user.last_name = 'Bederian'

        empl = Employee()
        empl.user = user
        empl.phone_number = '49291'
        empl.dni = '18999333'

        empl.save()

        return empl

    def createAdmin(self, username, passw):

        user = User.objects.create_user(username, '', passw)

        user.first_name = 'Carlos'
        user.last_name = 'Bederian'

        user.save()

        admin = Admin()
        admin.user = user
        admin.phone_number = '351123999'
        admin.dni = '17282282'

        admin.save()

        return admin

    def debug(self, res):
        """ Vos le pasas el res y debug te banca """

        print('\nEstado: ' + str(res.status_code))
        print('Redirecciones: ' + str(res.redirect_chain))

        known = False
        for templ in self.templates:
            if self.is_template(res, self.templates[templ]):
                known = True
                print('Página "' + templ + '" recibida.')
                break

        if not known:
            print('Página no conocida')

        msj = find_between(res.content, '<div class="alert alert-danger">', '</div>')
        msj2 = find_between(res.content, '<div class="alert alert-danger fade in">', '</div>')
        msj3 = find_between(res.content, '<div class="alert alert-success fade in">', '</div>')
        if msj:
            print('Mensaje: ' + msj.strip())
        if msj2:
            msj2 = msj2.strip()
            msj2 = find_between(msj2, '<a href="#" class="close" data-dismiss="alert" aria-label="close">&times;</a><center>', '</center>')
            print('Mensaje: ' + msj2.strip())
        if msj3:
            msj3 = find_between(msj3.strip(), '<a href="#" class="close" data-dismiss="alert" aria-label="close">&times;</a><center>', '</center>')
            print('Mensaje: ' + msj3.strip())

        f = open('respuesta.html', 'w')
        f.write(res.content)
        print('Respuesta guardada en "respuesta.html"')

    def is_template(self, res, filename, details=False):
        titles_m = self.titles_match(res, filename, details)

        # aca podrian haber otros chequeos ademas de los titulos

        return titles_m

    def titles_match(self, res, templ, details=False):

        template_title = self.get_template_title(templ)
        title_regs = map(reg_from_template,template_title)

        template_h1 = self.get_template_h1(templ)
        h1_regs = map(reg_from_template, template_h1)

        bar_content = self.get_content_title(res.content)
        bar_matches = map(lambda reg: bool(reg.match(bar_content)), title_regs)
        bar_title_matchs = not bar_content or any(bar_matches)

        h1_content = self.get_content_h1(res.content)
        h1_matches = map(lambda reg: bool(reg.match(h1_content)), h1_regs)
        h1_title_matchs = not h1_content or any(h1_matches)

        if details:
            print('bar content: "'+ str(self.get_content_title(res.content)) +'"')
            print('bar template: '+str(self.get_template_title(templ)))
            listofpatterns = map(lambda reg: reg.pattern, title_regs)
            print('bar regexp template: ' + str(listofpatterns))

            print('h1 content: "'+ str(self.get_content_h1(res.content)) +'"')
            print('h1 template: '+str(self.get_template_h1(templ)))
            listofpatterns = map(lambda reg: reg.pattern, h1_regs)
            print('h1 regexp template: ' + str(listofpatterns))

        return bar_title_matchs and h1_title_matchs


    def get_template_h1(self, templ):
        return get_template_string(templ, '<h1>', '</h1>')

    def get_content_h1(self, cont):
        return find_between(cont, '<h1>', '</h1>')

    def get_template_title(self, templ):
        return get_template_string(templ, '{% block title %}', '{% endblock title %}')

    def get_content_title(self, cont):
        return find_between(cont, '<title>', '</title>')


def get_template_string(templ, string1, string2):
    f =  open(APP_NAME + '/' + templ, 'r')
    template = f.read()

    strings = []
    while True:
        (s, end) = find_between(template, string1, string2, details=True)
        if not s:
            break
        strings.append(s)
        template = template[end:]

    return strings


def find_between(s, first, last, details=False):
    try:
        start = s.index(first) + len(first)
        end = s.index(last, start)

        string = s[start:end]
        if string[0] == ' ':
            string = string[1:]
        if string[-1] == ' ':
            string = string[:-1]

        if details:
            return (string, end)
        else:
            return string

    except ValueError:
        if details:
            return ('', 0)
        else:
            return ""


def reg_from_template(string):
    regexp = string
    while True:
        try:
            start = regexp.index('{{')
            end = regexp.index('}}')
        except:
            break
        if end < start:
            break
        regexp = regexp[:start] + '(.*)' + regexp[end+2:]
    return re.compile(regexp)
