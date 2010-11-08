#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from google.appengine.ext.webapp import util
import cgi
import datetime
import os
from google.appengine.ext.webapp import template
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.api import mail
import re


class Invoices(db.Model):
  service_number = db.StringProperty()
  customer_name = db.StringProperty(multiline=True)
  balance_due = db.FloatProperty()
  balance_paid = db.FloatProperty()
  owner = db.UserProperty()
  status = db.StringProperty()
  signature = db.StringProperty()
  start_date = db.DateTimeProperty()
  date = db.DateTimeProperty(auto_now_add=True)
  invoice = db.TextProperty()

class MainPage(webapp.RequestHandler):
  def get(self):
    user = users.get_current_user()
    if user:
      if users.is_current_user_admin():
        invoices = Invoices.gql("ORDER BY date DESC")
        total_due = 0.00
        for invoice in invoices:
          if(invoice.balance_due): 
            total_due += invoice.balance_due
        template_values = {
          'logout': users.create_logout_url("/"),
          'invoices': invoices,
          'total_due': total_due,
        }
        path = os.path.join(os.path.dirname(__file__), 'html/index.html')
        self.response.out.write(template.render(path, template_values))
      else:
        self.redirect(users.create_login_url(self.request.uri))
    else:
      self.redirect(users.create_login_url(self.request.uri))

class New(webapp.RequestHandler):
  def get(self):
    now = datetime.datetime.now()
    invoice = Invoices()
    while 1:
      service_number = str(now.strftime("%y%j")) + str(now.microsecond)
      q = db.GqlQuery("SELECT __key__ FROM Invoices where service_number = " + service_number)
      if q.count(1) == 0:
        break
    invoice.service_number = service_number
    invoice.start_date = invoice.date
    invoice.status = 'Pre Service'
    template_values = {
      'service_number': service_number,
    }
    path = os.path.join(os.path.dirname(__file__), 'html/invoicetemplate.html')
    invoice.invoice = template.render(path, template_values)
    invoice.put()
    address = "invoice?service_number="
    address += invoice.service_number
    self.redirect(address)

class Invoice(webapp.RequestHandler):
  def get(self):
    technicians = ''
    completed = ''
    in_progress = ''
    pre_service = ''
    customer = ''    
    service_number = self.request.get('service_number')
    q = Invoices.gql("where service_number = :number", number=service_number)
    user = users.get_current_user()
    for qr in q:
      if qr.status == 'In Progress':
        in_progress = """ selected="selected" """
        customer = "<p>This Service is in progress.</p>"
      elif qr.status == 'Pre Service':
        pre_service = """ selected="selected" """
        customer = "<p>This Service has not started yet.</p>"
      if qr.status == 'Completed':
        completed = """ selected="selected" """
        path = os.path.join(os.path.dirname(__file__), 'html/customer.html')
        customer = template.render(path, '')        
    invoicehtml = qr.invoice
    invoice_values = {
      'pre_service': pre_service,
      'in_progress': in_progress,
      'completed': completed,
    }
    path = os.path.join(os.path.dirname(__file__), 'html/technician.html')
    technicians = template.render(path, invoice_values)
    template_values = {
      'invoice': invoicehtml,
      'service_number': service_number,
      'notification': technicians if users.is_current_user_admin() else customer,
    }
    path = os.path.join(os.path.dirname(__file__), 'html/invoice.html')
    self.response.out.write(template.render(path, template_values))

  def post(self):
    user = users.get_current_user()
    now = datetime.datetime.now()
    updated_invoice = Invoices()
    service_number = self.request.get('service_number')
    query = Invoices.all()
    query.filter('service_number =', service_number)
    results = query.fetch(1)    
    if user:
      if users.is_current_user_admin():          
        for result in results:
          updated_invoice.start_date = result.start_date      
          updated_invoice.service_number = result.service_number
          updated_invoice.customer_name = self.request.get('customer_name')
          updated_invoice.balance_paid = float(self.request.get('paid'))
          updated_invoice.balance_due = float(self.request.get('due'))
          updated_invoice.invoice = self.request.get('invoice')
          updated_invoice.status = self.request.get('status')
          result.delete()
        updated_invoice.put()    
        self.response.out.write("Saved: " + str(now.strftime("%A, %B %d,  %Y %I:%M%p")))
    else:
      for result in results:
        result.signature = self.request.get('initials')
        result.put()
      self.response.out.write("Signed: " + str(now.strftime("%A, %B %d,  %Y %I:%M%p")))

application = webapp.WSGIApplication(
                                     [('/', MainPage),
                                      ('/new', New),
                                      ('/invoice', Invoice)],
                                     debug=True)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
