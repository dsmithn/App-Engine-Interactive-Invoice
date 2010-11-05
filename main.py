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
    invoice.invoice = """
<p style="text-align: center; color:#54ACD1; font-family: Geogria; font-size: 18pt;"><img id="image" src="/images/logo.png" alt="logo" /><br>
<a href="/spreadtheword.html" target="_blank">satistfied with your service?</a></p>
<div id="page-wrap">

		<textarea id="header">INVOICE</textarea>

		<div id="identity">

            <textarea id="address">Destin Smith-Norris
            
AltTech Support, LLC
16885 River Birch Cir
Delray Beach, Fl 33445

Phone: (561) 376-2588</textarea>
		</div>

		<div style="clear:both"></div>

		<div id="customer">

            <textarea id="customer-title">Customer Name</textarea>
<textarea id="customer-address">Enter customer address, email address and phone number</textarea>

            <table id="meta">
                <tr>
                    <td class="meta-head">Invoice #</td>
                    <td><div id="servicenumber">"""
    invoice.invoice += invoice.service_number
    invoice.invoice += """</div></td>
                </tr>
                <tr>

                    <td class="meta-head">Date</td>
                    <td><textarea id="date">December 15, 2009</textarea></td>
                </tr>
                <tr>
                    <td class="meta-head">Amount Due</td>
                    <td><div id="due" class="due">$875.00</div></td>
                </tr>

            </table>

		</div>

		<table id="items">

		  <tr>
		      <th>Item</th>
		      <th>Description</th>
		      <th>Unit Cost</th>
		      <th>Quantity</th>
		      <th>Price</th>
		  </tr>

		  <tr class="item-row">
		      <td class="item-name"><div class="delete-wpr"><textarea>complete computer rejuvenation</textarea><a class="delete" href="javascript:;" title="Remove row">X</a></div></td>
		      <td class="description"><textarea>Three hours of technical support (save $30)</textarea></td>
		      <td><textarea class="cost">$150.00</textarea></td>
		      <td><textarea class="qty">0</textarea></td>
		      <td><span class="price">$0.00</span></td>
		  </tr>

		  <tr class="item-row">
		      <td class="item-name"><div class="delete-wpr"><textarea>hourly service</textarea><a class="delete" href="javascript:;" title="Remove row">X</a></div></td>

		      <td class="description"><textarea>Onsite or remote technical support</textarea></td>
		      <td><textarea class="cost">$60.00</textarea></td>
		      <td><textarea class="qty">0</textarea></td>
		      <td><span class="price">$0.00</span></td>
		  </tr>

		  <tr class="item-row">
		      <td class="item-name"><div class="delete-wpr"><textarea>computer backup</textarea><a class="delete" href="javascript:;" title="Remove row">X</a></div></td>

		      <td class="description"><textarea>4GB Backup included in complete computer rejuvenation.  Documents and Desktop items are backed up.</textarea></td>
		      <td><textarea class="cost">$0.00</textarea></td>
		      <td><textarea class="qty">0</textarea></td>
		      <td><span class="price">$0.00</span></td>
		  </tr>

		  <tr class="item-row">
		      <td class="item-name"><div class="delete-wpr"><textarea>max computer backup</textarea><a class="delete" href="javascript:;" title="Remove row">X</a></div></td>
		      <td class="description"><textarea>320GB Backup.  Documents, pictures, music and Desktop items are backed up for all accounts on the computer.</textarea></td>
		      <td><textarea class="cost">$120.00</textarea></td>
		      <td><textarea class="qty">0</textarea></td>
		      <td><span class="price">$0.00</span></td>
		  </tr>
      
		  <tr class="item-row">
		      <td class="item-name"><div class="delete-wpr"><textarea>initial diagnosis</textarea><a class="delete" href="javascript:;" title="Remove row">X</a></div></td>

		      <td class="description"><textarea>Description of problems found and potential solutions.</textarea></td>
		      <td><textarea class="cost">$0.00</textarea></td>
		      <td><textarea class="qty">0</textarea></td>
		      <td><span class="price">$0.00</span></td>
		  </tr>
      
		  <tr class="item-row">
		      <td class="item-name"><div class="delete-wpr"><textarea>virus removal</textarea><a class="delete" href="javascript:;" title="Remove row">X</a></div></td>

		      <td class="description"><textarea>Download, install, update, and quickscan with MalwareBytes. It may be necessary to use advanced tools such as SysInternals, HijackThis or UBCD to fix persistant problems.</textarea></td>
		      <td><textarea class="cost">$0.00</textarea></td>
		      <td><textarea class="qty">0</textarea></td>
		      <td><span class="price">$0.00</span></td>
		  </tr>      
      
		  <tr class="item-row">
		      <td class="item-name"><div class="delete-wpr"><textarea>system tune-up</textarea><a class="delete" href="javascript:;" title="Remove row">X</a></div></td>
		      <td class="description"><textarea>Clean temparary files, clean registry, optionally erase history, fix invalid shortcuts, optimize startup items, check harddrive for errors, and uninstall any programs as requested.</textarea></td>
		      <td><textarea class="cost">$0.00</textarea></td>
		      <td><textarea class="qty">0</textarea></td>
		      <td><span class="price">$0.00</span></td>
		  </tr>      

		  <tr class="item-row">
		      <td class="item-name"><div class="delete-wpr"><textarea>wrap up</textarea><a class="delete" href="javascript:;" title="Remove row">X</a></div></td>

		      <td class="description"><textarea>Run full virus scan (if malware symptons found previous, update or install antivirus software, setup Windows Update to automatically update, analyze and defragment harddrive.</textarea></td>
		      <td><textarea class="cost">$0.00</textarea></td>
		      <td><textarea class="qty">0</textarea></td>
		      <td><span class="price">$0.00</span></td>
		  </tr>
      
		  <tr class="item-row">
		      <td class="item-name"><div class="delete-wpr"><textarea>final report</textarea><a class="delete" href="javascript:;" title="Remove row">X</a></div></td>
		      <td class="description"><textarea>Final report.</textarea></td>
		      <td><textarea class="cost">$0.00</textarea></td>
		      <td><textarea class="qty">0</textarea></td>
		      <td><span class="price">$0.00</span></td>
		  </tr>           

		  <tr id="hiderow">
		    <td colspan="5"><a id="addrow" href="javascript:;" title="Add a row">Add a row</a></td>
		  </tr>

		  <tr>
		      <td colspan="2" class="blank"> </td>
		      <td colspan="2" class="total-line">Subtotal</td>
		      <td class="total-value"><div id="subtotal">$875.00</div></td>
		  </tr>
		  <tr>

		      <td colspan="2" class="blank"> </td>
		      <td colspan="2" class="total-line">Total</td>
		      <td class="total-value"><div id="total">$875.00</div></td>
		  </tr>
		  <tr>
		      <td colspan="2" class="blank"> </td>
		      <td colspan="2" class="total-line">Amount Paid</td>

		      <td class="total-value"><textarea id="paid">$0.00</textarea></td>
		  </tr>
		  <tr>
		      <td colspan="2" class="blank"> </td>
		      <td colspan="2" class="total-line balance">Balance Due</td>
		      <td class="total-value balance"><div class="due">$875.00</div></td>
		  </tr>

		</table>

		<div id="terms">
		  <h5>Terms</h5>
		  <div style="text-align: left;">
      <p style="color:#54ACD1; font-family: Geogria; font-size: 18pt;">our guarantee to all clients<p>

      <strong>complete computer rejuvenation</strong><br>
      If the service you request cannot be completed successfully or you do not want to purchase needed hardware, $75 will be refunded to you and your computer will be returned with a complete diagnosis provided and the data backup if possible.<br>

      <strong>hourly services</strong><br>


      Our technicians will give you the best estimate for the maximum number of hours required for your specific needs, however it is impossible to know for sure and sometimes services run longer than expected. If you feel that your technician was not working as hard as he should have been to complete your service in the number of hours he quoted you, please contact us. If we feel that you were overcharged we will refund your excess hours over the technician's estimate. <br>
      <p style="color:#54ACD1; font-family: Geogria; font-size: 18pt;">support provided by alt+tech is governed by the following terms and conditions</p>
      <ul>
        <li>technical services are provided by local college students who are independent contractors</li>
        <li>support services may be provided onsite or remotely using your broadband internet connection</li>
        <li>you are 18 or older and have the right and capacity to bind yourself to these terms</li>
        <li>you are authorizing AltTech Support, LLC contractors to access and control your computer and peripherals for the purposes of diagnosis, service and repair and to make any modifications deemed necessary</li>
        <li>Alt+Tech Support does not provide data backup or restoration services and you are solely responsible for maintaining and backing up all information, data, text, photographs, music, and software stored on your computer prior to ordering the service</li>
        <li>services ordered will be pre-paid by either check or credit card</li>
        <li>alt+tech support, llc and its contractors will make their best good-faith efforts to provide the services specified</li>
        <li>if our fix doesn't work, call us back within 5 days and we will try and resolve it again at no additional cost</li>
        <li>for off-site services, if we cannot successfully complete the service or you do not wish to purchase necessary hardware, $75 will be refunded to you and your computer will be returned with a complete written diagnosis and the 4GB flash-drive data back-up (if possible)</li>
        <li>for remote services, if we cannot successfully complete the service after the second attempt, your entire purchase price will be refunded</li>
        <li>in no event shall alt+tech support, llc or its contractors be liable for any indirect, special, incidental, consequential, punitive or any other damages of any kind or nature arising directly or indirectly from the use of, or inability to use, the services, software, content or your personal computer including without limitation lost sales, lost revenue, loss profits or other loss of business or for loss or damage to data</li>
        <li>these terms are governed by the laws of the State of Florida</li>
      </ul>
      </div>
		</div>

</div>"""
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
    for qr in q:
      if qr.status == 'In Progress':
        technicians = """<p>
        <select id="status">
          <option value="Pre Service">Pre Service</option>
          <option value="In Progress" selected="selected">In Progress</option>
          <option value="Completed">Completed</option>
        </select>
        </p>
                    <p><input name="saveInvoice" type="button" value="Save Invoice" onClick="update()"> <div id="response"></div></p><br>
                    <p><input name="close" type="button" value="Close (Save First!)" onClick="parent.location='/'"> </p>"""
      if qr.status == 'Completed':
        technicians = """<p>
        <select id="status">
          <option value="Pre Service">Pre Service</option>
          <option value="In Progress">In Progress</option>
          <option value="Completed" selected="selected">Completed</option>
        </select>
        </p>
                    <p><input name="saveInvoice" type="button" value="Save Invoice" onClick="update()"> <div id="response"></div></p><br>
                    <p><input name="close" type="button" value="Close (Save First!)" onClick="parent.location='/'"> </p>"""
      elif qr.status == 'Pre Service':
        technicians = """<p>
        <select id="status">
          <option value="Pre Service" selected="selected">Pre Service</option>
          <option value="In Progress">In Progress</option>
          <option value="Completed">Completed</option>
        </select>
        </p>
                    <p><input name="saveInvoice" type="button" value="Save Invoice" onClick="update()"> <div id="response"></div></p><br>
                    <p><input name="close" type="button" value="Close (Save First!)" onClick="parent.location='/'"> </p>"""
      invoicehtml = qr.invoice
    if users.is_current_user_admin():
      template_values = {
        'invoice': invoicehtml,
        'technicians': technicians,
        }
    else:
      template_values = {
        'invoice': invoicehtml,
        'technicians': '',
        }

    path = os.path.join(os.path.dirname(__file__), 'html/invoice.html')
    self.response.out.write(template.render(path, template_values))

  def post(self):
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

application = webapp.WSGIApplication(
                                     [('/', MainPage),
                                      ('/new', New),
                                      ('/invoice', Invoice)],
                                     debug=True)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
