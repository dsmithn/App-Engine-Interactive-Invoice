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
    self.response.out.write('<html><body>')
    user = users.get_current_user()
    if user:
      if users.is_current_user_admin():
        self.response.out.write("""<p> <input name="NewInvoice" type="button" value="New Invoice" onClick="location.href='/new'"> </p> """)
        self.response.out.write("<p><a href=\"%s\">sign out</a></p>" % users.create_logout_url("/"))
        invoices = Invoices.gql("ORDER BY date DESC")
        output = '<br><table border="1"><th>Service Number</th><th>Status</th><th>Signature</th><th>Customer Name</th><th>Amount Paid</th><th>Amount Due</th><th>Last Activity</th><th>Start Date</th>'
        total_due = 0.00
        for invoice in invoices:
          output += '<tr><td><a href="/invoice?service_number=%s">%s<a>' % (invoice.service_number,invoice.service_number)
          output += '</td><td>' + str(invoice.status)
          output += '</td><td>' + str(invoice.signature)
          output += '</td><td>' + str(invoice.customer_name)
          output += '</td><td>$' + str(invoice.balance_paid)          
          output += '</td><td><span style="color: #FF0000;">$' + str(invoice.balance_due)
          if(invoice.balance_due): 
            total_due += invoice.balance_due
          output += '</td><td>' + str(invoice.date)
          output += '</span></td><td>     ' + str(invoice.start_date) + '</td></tr>'
        output += """</table>
          </body>
          </html>"""
        self.response.out.write('Unpaid Total: <span style="color: #FF0000;">$' + str(total_due) + '</span><br>')
        self.response.out.write(output)
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
    service_number = self.request.get('service_number')
    q = Invoices.gql("where service_number = :number", number=service_number)
    user = users.get_current_user()
    completed = ''
    in_progress = ''
    pre_service = ''
    for qr in q:
      if qr.status == 'In Progress':
        in_progress = """ selected="selected" """
      if qr.status == 'Completed':
        completed = """ selected="selected" """
      elif qr.status == 'Pre Service':
        pre_service = """ selected="selected" """
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
      'technicians': technicians if users.is_current_user_admin() else '',
    }
    path = os.path.join(os.path.dirname(__file__), 'html/invoice.html')
    self.response.out.write(template.render(path, template_values))

  def post(self):
    user = users.get_current_user()
    if user:
      if users.is_current_user_admin():  
        now = datetime.datetime.now()
        updated_invoice = Invoices()
        service_number = self.request.get('service_number')
        query = Invoices.all()
        query.filter('service_number =', service_number)
        results = query.fetch(1)
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
      self.response.out.write("Error: Not logged in as admin.")

application = webapp.WSGIApplication(
                                     [('/', MainPage),
                                      ('/new', New),
                                      ('/invoice', Invoice)],
                                     debug=True)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
