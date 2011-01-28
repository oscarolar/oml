# -*- encoding: utf-8 -*-
################################################
#
# OpenERP, Open Source Management Solution
# Copyright (c) 2010 moylop260 (moylop260@hotmail.com) All Rights Reserved.
# info <moylop260@hotmail.com>
# 
# $Id$
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see http://www.gnu.org/licenses/.
#
##############################################################################

from osv import osv
from osv import fields
from tools import amount_to_text
import tools
import time
from xml.dom import minidom
import os
import base64
#import libxml2
#import libxslt
#import zipfile
#import StringIO
#import OpenSSL
import hashlib
import tempfile
import os
import netsvc



def exec_command_pipe(name, *args):
    #Agregue esta funcion, ya que con la nueva funcion original, de tools no funciona
    prog = tools.find_in_path(name)
    if not prog:
        raise Exception('Couldn\'t find %s' % name)
    if os.name == "nt":
        cmd = '"'+prog+'" '+' '.join(args)
    else:
        cmd = prog+' '+' '.join(args)
    return os.popen2(cmd, 'b')

def find_in_subpath(name, subpath):
    if os.path.isdir( subpath ):
        path = [dir for dir in map(lambda x: os.path.join(subpath, x), os.listdir(subpath) )
                if os.path.isdir(dir)]
        for dir in path:
            val = os.path.join(dir, name)
            if os.path.isfile(val) or os.path.islink(val):
                return val
    return None

def conv_ascii(text):
    """Convierte vocales accentuadas, ñ y ç a sus caracteres equivalentes ASCII"""
    old_chars = ['á','é','í','ó','ú','à','è','ì','ò','ù','ä','ë','ï','ö','ü','â','ê','î', \
        'ô','û','Á','É','Í','Ú','Ó','À','È','Ì','Ò','Ù','Ä','Ë','Ï','Ö','Ü','Â','Ê','Î',\
        'Ô','Û','ñ','Ñ','ç','Ç','ª','º'
    ]
    new_chars = ['a','e','i','o','u','a','e','i','o','u','a','e','i','o','u','a','e','i','o',\
        'u','A','E','I','O','U','A','E','I','O','U','A','E','I','O','U','A','E','I','O','U','n',\
        'N','c','C','a','o'
    ]
    for old, new in zip(old_chars, new_chars):
        try:
            text = text.replace(unicode(old,'UTF-8'), new)
        except:
            text = text.replace(old, new)
    return text

class account_payment_term(osv.osv):
    _inherit = "account.payment.term"
    
    def compute(self, cr, uid, id, value, date_ref=False, context={}):
        if date_ref:
            try:
                date_ref = time.strftime('%Y-%m-%d', time.strptime(date_ref, '%Y-%m-%d %H:%M:%S'))
            except:
                pass
        return super(account_payment_term, self).compute(cr, uid, id, value, date_ref, context=context)
account_payment_term()

msg2= "Contacte a su administrador y/o a moylop260@hotmail.com"

class account_invoice(osv.osv):
    _inherit = 'account.invoice'
    """
    def action_number(self, cr, uid, ids, *args):
        cr.execute('SELECT id, type, number, move_id, reference ' \
                'FROM account_invoice ' \
                'WHERE id IN ('+','.join(map(str,ids))+')')
        obj_inv = self.browse(cr, uid, ids)[0]
        for (id, invtype, number, move_id, reference) in cr.fetchall():
            if not number:
                tmp_context = {
                    #'fiscalyear_id' : obj_inv.period_id.fiscalyear_id.id,
                }
                if obj_inv.journal_id.invoice_sequence_id:
                    sid = obj_inv.journal_id.invoice_sequence_id.id
                    number = self.pool.get('ir.sequence').get_id(cr, uid, sid, 'id=%s', context=tmp_context)
                else:
                    number = self.pool.get('ir.sequence').get_id(cr, uid,
                                                                 'account.invoice.' + invtype,
                                                                 'code=%s',
                                                                 context=tmp_context)
                if not number:
                    raise osv.except_osv(_('Warning !'), _('There is no active invoice sequence defined for the journal !'))
                if invtype in ('in_invoice', 'in_refund'):
                    ref = reference
                else:
                    ref = self._convert_ref(cr, uid, number)
                cr.execute('UPDATE account_invoice SET number=%s ' \
                        'WHERE id=%d', (number, id))
                cr.execute('UPDATE account_move_line SET ref=%s ' \
                        'WHERE move_id=%d AND (ref is null OR ref = \'\')',
                        (ref, move_id))
                cr.execute('UPDATE account_analytic_line SET ref=%s ' \
                        'FROM account_move_line ' \
                        'WHERE account_move_line.move_id = %d ' \
                            'AND account_analytic_line.move_id = account_move_line.id',
                            (ref, move_id))
        return True
    """
    
    def _get_invoice_sequence(self, cr, uid, ids, field_names=None, arg=False, context={}):
        if not context:
            context = {}
        res = {}
        for invoice in self.browse(cr, uid, ids):
            sequence_id = False
            company = invoice.company_id
            while True:
                if invoice.type == 'out_invoice':
                    sequence_id = company.invoice_out_sequence_id
                elif invoice.type == 'out_refund':
                    sequence_id = company.invoice_out_refund_sequence_id
                company = company.parent_id
                if sequence_id or not company:
                    break
            if not sequence_id:
                sequence_id = invoice.journal_id.invoice_sequence_id
            sequence_id = sequence_id and sequence_id.id or False
            if not sequence_id:
                sequence_str = 'account.invoice.' + invoice.type
                test = 'code=%s'
                cr.execute('SELECT id FROM ir_sequence WHERE '+test+' AND active=%s LIMIT 1', (sequence_str, True))
                res2 = cr.dictfetchone()
                sequence_id = res2 and res2['id'] or False
            res[invoice.id] = sequence_id
        return res
    """
    def action_number(self, cr, uid, ids, context=None):#usando super
        if not context:
            context = {}
        self._attach_invoice(cr, uid, ids)#Linea agregada
        return res
    """
    def action_number(self, cr, uid, ids, *args):
        invoice_id__sequence_id = self._get_invoice_sequence(cr, uid, ids)#Linea agregada
        #Sustituye a la funcion original, es el mismo codigo, solo le agrega unas lineas, y no hacer SUPER
        """OpenERP
        cr.execute('SELECT id, type, number, move_id, reference ' \
                   'FROM account_invoice ' \
                   'WHERE id IN %s',
                   (tuple(ids),))
        """
        #TinyERP compatibility
        cr.execute('SELECT id, type, number, move_id, reference ' \
                'FROM account_invoice ' \
                'WHERE id IN ('+','.join(map(str,ids))+')')
        obj_inv = self.browse(cr, uid, ids)[0]
        for (id, invtype, number, move_id, reference) in cr.fetchall():
            if not number:
                tmp_context = {
                    'fiscalyear_id' : obj_inv.period_id and obj_inv.period_id.fiscalyear_id and obj_inv.period_id.fiscalyear_id.id or False,
                }
                """
                #if obj_inv.journal_id.invoice_sequence_id:#Original line code
                if obj_inv.journal_id.invoice_sequence_id or invoice_id__sequence_id[id]:#Agregue esta linea
                    #sid = obj_inv.journal_id.invoice_sequence_id.id#Original line code
                    sid = invoice_id__sequence_id[id] or obj_inv.journal_id.invoice_sequence_id.id#Esta es la linea modificada
                    number = self.pool.get('ir.sequence').get_id(cr, uid, sid, 'id=%s', context=tmp_context)
                else:
                    number = self.pool.get('ir.sequence').get_id(cr, uid,
                                                                 'account.invoice.' + invtype,
                                                                 'code=%s',
                                                                 context=tmp_context)
                """
                sid = invoice_id__sequence_id[id]
                if sid:
                    number = self.pool.get('ir.sequence').get_id(cr, uid, sid, 'id=%s', context=tmp_context)
                if not number:
                    raise osv.except_osv('Warning !', 'No hay una secuencia de folios, definida !')

                if invtype in ('in_invoice', 'in_refund'):
                    ref = reference
                else:
                    ref = self._convert_ref(cr, uid, number)
                cr.execute('UPDATE account_invoice SET number=%s ' \
                        'WHERE id=%s', (number, id))
                cr.execute('UPDATE account_move SET ref=%s ' \
                        'WHERE id=%s AND (ref is null OR ref = \'\')',
                        (ref, move_id))
                cr.execute('UPDATE account_move_line SET ref=%s ' \
                        'WHERE move_id=%s AND (ref is null OR ref = \'\')',
                        (ref, move_id))
                cr.execute('UPDATE account_analytic_line SET ref=%s ' \
                        'FROM account_move_line ' \
                        'WHERE account_move_line.move_id = %s ' \
                            'AND account_analytic_line.move_id = account_move_line.id',
                            (ref, move_id))
        return True
    
    
    def create_report(self, cr, uid, res_ids, report_name=False, file_name=False):
        if not report_name or not res_ids:
            return (False,Exception('Report name and Resources ids are required !!!'))
        #try:
        ret_file_name = file_name+'.pdf'
        service = netsvc.LocalService("report."+report_name);
        (result,format) = service.create(cr, uid, res_ids, {}, {})
        fp = open(ret_file_name,'wb+');
        fp.write(result);
        fp.close();
        #except Exception,e:
            #print 'Exception in create report:',e
            #return (False,str(e))
        return (True,ret_file_name)
    
    def create_report_pdf(self, cr, uid, ids, context={}):
        if not context:
            context = {}
        id = ids[0]
        
        (fileno, fname) = tempfile.mkstemp('.pdf', 'openerp_' + (False or '') + '__facturae__' )
        os.close( fileno )
        
        file = self.create_report(cr, uid, [id], "account.invoice.facturae.pdf", fname)
        is_file = file[0]
        fname = file[1]
        if is_file and os.path.isfile(fname):
            f = open(fname, "r")
            data = f.read()
            f.close()
            
            data_attach = {
                'name': context.get('fname'),
                'datas': data and base64.encodestring( data ) or None,
                'datas_fname': context.get('fname'),
                'description': 'Factura-E PDF',
                'res_model': self._name,
                'res_id': id,
            }
            self.pool.get('ir.attachment').create(cr, uid, data_attach, context=context)
        return True
        
    def action_make_cfd(self, cr, uid, ids, *args):
        self._attach_invoice(cr, uid, ids)
        return True
    
    def ________action_number(self, cr, uid, ids, *args):
        cr.execute('SELECT id, type, number, move_id, reference ' \
                'FROM account_invoice ' \
                'WHERE id IN ('+','.join(map(str,ids))+')')
        obj_inv = self.browse(cr, uid, ids)[0]
        
        invoice_id__sequence_id = self._get_sequence(cr, uid, ids)##agregado
        
        for (id, invtype, number, move_id, reference) in cr.fetchall():
            if not number:
                tmp_context = {
                    'fiscalyear_id' : obj_inv.period_id.fiscalyear_id.id,
                }
                if invoice_id__sequence_id[id]:
                    sid = invoice_id__sequence_id[id]
                    number = self.pool.get('ir.sequence').get_id(cr, uid, sid, 'id=%s', context=tmp_context)
                elif obj_inv.journal_id.invoice_sequence_id:
                    sid = obj_inv.journal_id.invoice_sequence_id.id
                    number = self.pool.get('ir.sequence').get_id(cr, uid, sid, 'id=%s', context=tmp_context)
                else:
                    number = self.pool.get('ir.sequence').get_id(cr, uid,
                                                                 'account.invoice.' + invtype,
                                                                 'code=%s',
                                                                 context=tmp_context)
                if not number:
                    raise osv.except_osv('Warning !', 'No hay una secuencia de folios bien definida. !')
                if invtype in ('in_invoice', 'in_refund'):
                    ref = reference
                else:
                    ref = self._convert_ref(cr, uid, number)
                cr.execute('UPDATE account_invoice SET number=%s ' \
                        'WHERE id=%d', (number, id))
                cr.execute('UPDATE account_move_line SET ref=%s ' \
                        'WHERE move_id=%d AND (ref is null OR ref = \'\')',
                        (ref, move_id))
                cr.execute('UPDATE account_analytic_line SET ref=%s ' \
                        'FROM account_move_line ' \
                        'WHERE account_move_line.move_id = %d ' \
                            'AND account_analytic_line.move_id = account_move_line.id',
                            (ref, move_id))
        return True
    
    def _attach_invoice(self, cr, uid, ids, context=None):
        if not context:
            context = {}
        inv_type_facturae = {'out_invoice': True, 'out_refund': True, 'in_invoice': False, 'in_refund': False}
        for inv in self.browse(cr, uid, ids):
            if inv_type_facturae.get(inv.type, False):
                fname, xml_data = self.pool.get('account.invoice')._get_facturae_invoice_xml_data(cr, uid, [inv.id], context=context)
                data_attach = {
                        'name': fname,
                        #'datas':binascii.b2a_base64(str(attachents.get(attactment))),
                        'datas': xml_data and base64.encodestring( xml_data ) or None,
                        'datas_fname': fname,
                        'description': 'Factura-E XML',
                        'res_model': self._name,
                        'res_id': inv.id,
                }
                self.pool.get('ir.attachment').create(cr, uid, data_attach, context=context)
                fname = fname.replace('.xml', '.pdf')
                self.create_report_pdf(cr, uid, ids, context={'fname': fname})
        return True
    
    def action_move_create(self, cr, uid, ids, *args):
        for inv in self.browse(cr, uid, ids):
            if inv.move_id:
                continue
            if not inv.date_invoice:
                self.write(cr, uid, [inv.id], {'date_invoice': time.strftime('%Y-%m-%d %H:%M:%S')})
        return super(account_invoice, self).action_move_create(cr, uid, ids, *args)
    
    def _get_fname_invoice(self, cr, uid, ids, field_names=None, arg=False, context={}):
        res = {}
        sequence_obj = self.pool.get('ir.sequence')
        
        invoice_id__sequence_id = self._get_invoice_sequence(cr, uid, ids, context=context)
        for invoice in self.browse(cr, uid, ids, context=context):
            sequence_id = invoice_id__sequence_id[invoice.id]
            sequence = False
            if sequence_id:
                sequence = sequence_obj.browse(cr, uid, [sequence_id], context)[0]
            fname = ""
            fname += (invoice.company_id.partner_id and invoice.company_id.partner_id.vat or '')
            fname += '.'
            fname += sequence and sequence.approval_id and sequence.approval_id.serie or ''
            fname += '.'
            fname += invoice.number or ''
            res[invoice.id] = fname
        return res
        
    def action_cancel_draft(self, cr, uid, ids, *args):
        attachment_obj = self.pool.get('ir.attachment')
        for invoice in self.browse(cr, uid, ids):
            try:
                attachment_xml_id = attachment_obj.search(cr, uid, [
                    ('name','=',invoice.fname_invoice+'.xml'),
                    ('datas_fname','=',invoice.fname_invoice+'.xml'),
                    ('res_model','=','account.invoice'),
                    ('res_id','=',invoice.id)
                ], limit=1)
                attachment_obj.unlink(cr, uid, attachment_xml_id)
                
                attachment_pdf_id = attachment_obj.search(cr, uid, [
                    ('name','=',invoice.fname_invoice),###no se agrega.pdf, porque el generador de reportes, no lo hace asi, actualmente o agrega doble .pdf o nada
                    #('name','=',invoice.fname_invoice+'.pdf'),
                    ('datas_fname','=',invoice.fname_invoice+'.pdf'),
                    ('res_model','=','account.invoice'),
                    ('res_id','=',invoice.id)
                ], limit=1)
                attachment_obj.unlink(cr, uid, attachment_pdf_id)
            except:
                pass
        return super(account_invoice, self).action_cancel_draft(cr, uid, ids, args)
        
    _columns = {
        ##Extract date_invoice from original, but add datetime
        'date_invoice': fields.datetime('Date Invoiced', states={'open':[('readonly',True)],'close':[('readonly',True)]}, help="Keep empty to use the current date"),
        'invoice_sequence_id': fields.function(_get_invoice_sequence, method=True, type='many2one', relation='ir.sequence', string='Invoice Sequence', store=True),
        'fname_invoice':  fields.function(_get_fname_invoice, method=True, type='char', size='26', string='File Name Invoice'),
    }
    
    _defaults = {
        'date_invoice': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
    }
    
    def binary2file(self, cr, uid, ids, binary_data, file_prefix="", file_suffix=""):
        (fileno, fname) = tempfile.mkstemp(file_suffix, file_prefix)
        f = open( fname, 'w' )
        f.write( base64.decodestring( binary_data ) )
        f.close()
        os.close( fileno )
        return fname
    
    def _get_file_globals(self, cr, uid, ids, context={}):
        id = ids and ids[0] or False
        file_globals = {}
        if id:
            invoice = self.browse(cr, uid, id, context=context)
            #certificate_id = invoice.company_id.certificate_id
            certificate_id = self.pool.get('res.company')._get_current_certificate(cr, uid, [invoice.company_id.id], field_names=None, arg=False, context=context)[invoice.company_id.id]
            certificate_id = certificate_id and self.pool.get('res.company.facturae.certificate').browse(cr, uid, [certificate_id], context=context)[0] or False
            
            if certificate_id:
                if not certificate_id.certificate_file_pem:
                    #generate certificate_id.certificate_file_pem, a partir del certificate_id.certificate_file
                    pass
                try:
                    fname_cer_pem = self.binary2file(cr, uid, ids, certificate_id.certificate_file_pem, 'openerp_' + (certificate_id.serial_number or '') + '__certificate__', '.cer.pem')
                except:
                    raise osv.except_osv('Error !', 'No se ha capturado un archivo CERTIFICADO en formato PEM, en la company!')
                file_globals['fname_cer_pem'] = fname_cer_pem
                file_globals['fname_cer'] = fname_cer_pem
                try:
                    fname_key_pem = self.binary2file(cr, uid, ids, certificate_id.certificate_key_file_pem, 'openerp_' + (certificate_id.serial_number or '') + '__certificate__', '.key.pem')
                except:
                    raise osv.except_osv('Error !', 'No se ha capturado un archivo KEY en formato PEM, en la company!')
                file_globals['fname_key_pem'] = fname_key_pem
                file_globals['fname_key'] = fname_key_pem
                
                if certificate_id.fname_xslt:
                    if ( certificate_id.fname_xslt[0] == os.sep or certificate_id.fname_xslt[1] == ':' ):
                        file_globals['fname_xslt'] = certificate_id.fname_xslt
                    else:
                        file_globals['fname_xslt'] = os.path.join( tools.config["root_path"], certificate_id.fname_xslt )
                else:
                    file_globals['fname_xslt'] = os.path.join( tools.config["addons_path"], 'l10n_mx_facturae', 'SAT', 'cadenaoriginal_2_0_l.xslt' )
                
                if not file_globals.get('fname_xslt', False):
                    raise osv.except_osv('Warning !', 'No se ha definido fname_xslt. !')
                
                if not os.path.isfile(file_globals.get('fname_xslt', ' ')):
                    raise osv.except_osv('Warning !', 'No existe el archivo [%s]. !'%(file_globals.get('fname_xslt', ' ')))
                
                file_globals['serial_number'] = certificate_id.serial_number
            else:
                raise osv.except_osv('Warning !', 'No se tiene un certificado valido\nVerique las fechas del certificado, y que este activo, %s !'%(msg2))
        return file_globals
    
    def _get_facturae_invoice_txt_data(self, cr, uid, ids, context={}):
        facturae_datas = self._get_facturae_invoice_dict_data(cr, uid, ids, context=context)
        facturae_data_txt_lists = []
        folio_data = self._get_folio(cr, uid, ids, context=context)
        facturae_type_dict = {'out_invoice': 'I', 'out_refund': 'E', 'in_invoice': False, 'in_refund': False}
        fechas = []
        for facturae_data in facturae_datas:
            invoice_comprobante_data = facturae_data['Comprobante']
            fechas.append( invoice_comprobante_data['fecha'] )
            if facturae_data['state'] in ['open', 'paid']:
                facturae_state = 1
            elif facturae_data['state'] in ['cancel']:
                facturae_state = 0
            else:
                continue
            facturae_type = facturae_type_dict[ facturae_data['type'] ]
            if not facturae_type:
                continue
            #if not invoice_comprobante_data['Receptor']['rfc']:
                #raise osv.except_osv('Warning !', 'No se tiene definido el RFC de la factura [%s].\n%s !'%(facturae_data['Comprobante']['folio'], msg2))
            facturae_data_txt_list = [
                invoice_comprobante_data['Receptor']['rfc'] or '',
                invoice_comprobante_data['serie'] or '',
                invoice_comprobante_data['folio'] or '',
                str( invoice_comprobante_data['anoAprobacion'] ) + str( invoice_comprobante_data['noAprobacion'] ),
                time.strftime('%d/%m/%Y %H:%M:%S', time.strptime( facturae_data['date_invoice'], '%Y-%m-%d %H:%M:%S')),#invoice_comprobante_data['fecha'].replace('T', ' '),
                invoice_comprobante_data['total'] or 0.0,
                invoice_comprobante_data['Impuestos']['totalImpuestosTrasladados'] or 0.0,
                facturae_state,
                facturae_type,
                '',
            ]
            facturae_data_txt_lists.append( facturae_data_txt_list )
        
        fecha_promedio = time.strftime('%Y-%m-%d')
        if fechas:
            fecha_promedio = fechas[ int( len(fechas)/2 )-1 ]
        
        cad = ""
        for facturae_data_txt in facturae_data_txt_lists:
            cad += '|'
            cad += '|'.join(map(lambda x: str(x) or '||', facturae_data_txt))
            cad += '|'
            cad += '\r\n'
        
        fname = "1" + invoice_comprobante_data['Emisor']['rfc'] + '-' + time.strftime('%m%Y', time.strptime(fecha_promedio, '%Y-%m-%dT%H:%M:%S')) + '.txt'
        return cad, fname
    
    def _get_folio(self, cr, uid, ids, context={}):
        folio_data = {}
        id = ids and ids[0] or False
        if id:
            invoice = self.browse(cr, uid, id, context=context)
            """
            def get_id(self, cr, uid, sequence_id, test='id=%s', context=None):
                if test not in ('id=%s', 'code=%s'):
                    raise ValueError('invalid test')
                cr.execute('SELECT id, number_next, prefix, suffix, padding FROM ir_sequence WHERE '+test+' AND active=%s FOR UPDATE', (sequence_id, True))
                res = cr.dictfetchone()
                if res:
            """
            """
            tmp_context = {
                'fiscalyear_id' : invoice.period_id.fiscalyear_id.id,
            }
            if invoice.journal_id.invoice_sequence_id:
                sid = invoice.journal_id.invoice_sequence_id.id
                number = self.pool.get('ir.sequence').get_id(cr, uid, sid, 'id=%s', context=tmp_context)
            else:
                number = self.pool.get('ir.sequence').get_id(cr, uid,
                                                             'account.invoice.' + invtype,
                                                             'code=%s',
                                                             context=tmp_context)
                                                                 
            if not number:
                raise osv.except_osv('Warning !', 'There is no active invoice sequence defined for the journal !')
            """
            sequence_id = self._get_invoice_sequence(cr, uid, [id])[id]
            """
            if invoice.journal_id.invoice_sequence_id or invoice_id__sequence_id[id]:
                sequence_id = invoice_id__sequence_id[id] or invoice.journal_id.invoice_sequence_id.id
            else:
                test = 'code=%s'
                test_value = 'account.invoice.' + invoice.type
                test2 = '\n--company_id=%s\n'
                test2_value = invoice.company_id.id
                cr.execute('SELECT id, number_next, prefix, suffix, padding FROM ir_sequence WHERE '+test + test2+ ' AND active=%s FOR UPDATE', (test_value, test2_value, True))
                res = cr.dictfetchone()
                sequence_id = res and res['id'] or False
            """
            if sequence_id:
                #NO ES COMPATIBLE CON TINYERP approval_id = sequence.approval_id.id
                approval_id = self.pool.get('ir.sequence')._get_current_approval(cr, uid, [sequence_id], field_names=None, arg=False, context=context)[sequence_id]
                approval = approval_id and self.pool.get('ir.sequence.approval').browse(cr, uid, [approval_id], context=context)[0] or False
                if approval:
                    folio_data = {
                        'serie': approval.serie,
                        #'folio': '1',
                        'noAprobacion': approval.approval_number,
                        'anoAprobacion': approval.approval_year,
                        'desde': approval.number_start,
                        'hasta': approval.number_end,
                        #'noCertificado': "30001000000100000800",
                    }
                else:
                    raise osv.except_osv('Warning !', 'La secuencia no tiene datos de facturacion electronica.\nEn la sequence_id [%d].\n %s !'%(sequence_id, msg2))
            else:
                raise osv.except_osv('Warning !', 'No se encontro un sequence de configuracion. %s !'%(msg2))
        return folio_data
    
    def _dict_iteritems_sort(self, data_dict):#cr=False, uid=False, ids=[], context={}):
        key_order = [
            'Emisor',
            'Receptor',
            'Conceptos',
            'Impuestos',
        ]
        keys = data_dict.keys()
        key_item_sort = []
        for ko in key_order:
            if ko in keys:
                key_item_sort.append( [ko, data_dict[ko]] )
                keys.pop( keys.index( ko ) )
        for key_too in keys:
            key_item_sort.append( [key_too, data_dict[key_too]] )
        return key_item_sort
    
    def dict2xml(self, data_dict, node=False, doc=False):
        parent = False
        if node:
            parent = True
        
        for element, attribute in self._dict_iteritems_sort( data_dict ):
            if not parent:
                doc = minidom.Document()
            if isinstance( attribute, dict ):
                if not parent:
                    node = doc.createElement( element )
                    self.dict2xml( attribute, node, doc )
                else:
                    child = doc.createElement( element )
                    self.dict2xml( attribute, child, doc )
                    node.appendChild(child)
            elif isinstance( attribute, list):
                child = doc.createElement( element )
                for attr in attribute:
                    if isinstance( attr, dict ):
                        self.dict2xml( attr, child, doc )
                node.appendChild(child)
            else:
                if isinstance(attribute, str) or isinstance(attribute, unicode) :
                    attribute = conv_ascii(attribute)
                else:
                        attribute = str(attribute)
                node.setAttribute(element, attribute)
                #print "attribute",unicode( attribute, 'UTF-8')
        if not parent:
            doc.appendChild(node)
        return doc

    def _get_facturae_invoice_xml_data(self, cr, uid, ids, context={}):
        if not context:
            context = {}
        data_dict = self._get_facturae_invoice_dict_data(cr, uid, ids, context=context)[0]
        doc_xml = self.dict2xml( {'Comprobante': data_dict.get('Comprobante') } )
        invoice_number = "sn"
        (fileno_xml, fname_xml) = tempfile.mkstemp('.xml', 'openerp_' + (invoice_number or '') + '__facturae__' )
        fname_txt =  fname_xml + '.txt'
        f = open(fname_xml, 'w')
        doc_xml.writexml(f, indent='    ', addindent='    ', newl='\r\n', encoding='UTF-8')
        f.close()
        os.close(fileno_xml)
        
        (fileno_sign, fname_sign) = tempfile.mkstemp('.txt', 'openerp_' + (invoice_number or '') + '__facturae_txt_md5__' )
        os.close(fileno_sign)
        
        context.update({
            'fname_xml': fname_xml,
            'fname_txt': fname_txt,
            'fname_sign': fname_sign,
        })
        context.update( self._get_file_globals(cr, uid, ids, context=context) )
        fname_txt, txt_str = self._xml2cad_orig(cr=False, uid=False, ids=False, context=context)
        data_dict['cadena_original'] = txt_str
        
        #time.strftime('%Y-%m-%dT%H:%M:%S', time.strptime(invoice.date_invoice, '%Y-%m-%d %H:%M:%S'))
        context.update( { 'fecha': data_dict['Comprobante']['fecha'] } )
        sign_str = self._get_sello(cr=False, uid=False, ids=False, context=context)
        if not sign_str:
            raise osv.except_osv('Error en Sello !', 'No se pudo generar el sello del comprobante.\nVerifique su configuracion.\ns%s'%(msg2))
        
        nodeComprobante = doc_xml.getElementsByTagName("Comprobante")[0]
        nodeComprobante.setAttribute("sello", sign_str)
        data_dict['Comprobante']['sello'] = sign_str
        
        noCertificado = self._get_noCertificado( context['fname_cer'] )
        if not noCertificado:
            raise osv.except_osv('Error en No Certificado !', 'No se pudo obtener el No de Certificado del comprobante.\nVerifique su configuracion.\n%s'%(msg2))
        nodeComprobante.setAttribute("noCertificado", noCertificado)
        data_dict['Comprobante']['noCertificado'] = noCertificado
        
        cert_str = self._get_certificate_str( context['fname_cer'] )
        if not cert_str:
            raise osv.except_osv('Error en Certificado!', 'No se pudo generar el Certificado del comprobante.\nVerifique su configuracion.\n%s'%(msg2))
        nodeComprobante.setAttribute("certificado", cert_str)
        data_dict['Comprobante']['certificado'] = cert_str
        
        if not data_dict['Comprobante'].get('folio', ''):
            raise osv.except_osv('Error en Folio!', 'No se pudo obtener el Folio del comprobante.\nVerifique su configuracion.\n%s'%(msg2))
        
        if context.get('type_data') == 'dict':
            return data_dict
        if context.get('type_data') == 'xml_obj':
            return doc_xml
        data_xml = doc_xml.toxml('UTF-8')
        fname_xml = (data_dict['Comprobante']['Emisor']['rfc'] or '') + '.' + ( data_dict['Comprobante'].get('serie', '') or '') + '.' + ( data_dict['Comprobante'].get('folio', '') or '') + '.xml'
        return fname_xml, data_xml

    def _get_noCertificado(self, fname_cer, pem=True):
        """
        fcer = open(fname_cer, "r")
        filetype = pem and OpenSSL.crypto.FILETYPE_PEM or OpenSSL.crypto.FILETYPE_ASN1
        cer = OpenSSL.crypto.load_certificate(filetype, fcer.read())
        serial_number_hex_str = hex( cer.get_serial_number() )
        #serial_number_fmt_str = '3' + serial_number_hex_str.replace('3', '').replace('0x', '').replace('L', '')
        serial_number_fmt_str = serial_number_hex_str.replace('3', '').replace('0x', '').replace('L', '')
        fcer.close()
        return serial_number_fmt_str
        """
        if os.name == "nt":
            prog_openssl = 'openssl.exe'
        else:
            prog_openssl = 'openssl'
        
        subpath = os.path.join( tools.config["addons_path"], 'l10n_mx_facturae', 'depends_app')
        prog_openssl_fullpath = tools.find_in_path( prog_openssl ) or find_in_subpath(prog_openssl, subpath) or prog_openssl
        
        #(fileno, fname_no_cert) = tempfile.mkstemp("no_cert", "__openerp_cfd__")
        #f = open( fname_no_cert, 'w' )
        #f.close( )
        #os.close( fileno )
        
        (fileno_serial_number_cert, fname_serial_number_cert) = tempfile.mkstemp('.txt', 'openerp_' + (False or '') + '__facturae_serial_number_cert__' )
        os.close(fileno_serial_number_cert)
        
        (fileno_serial_number_cert_bat, fname_serial_number_cert_bat) = tempfile.mkstemp('.txt.bat', 'openerp_' + (False or '') + '__facturae_serial_number_cert__' )
        os.close(fileno_serial_number_cert_bat)
        
        cmd = 'x509 -in "%s" -serial -noout > "%s"'%(fname_cer, fname_serial_number_cert)
        if os.name == "nt":
            f = open(fname_serial_number_cert_bat, 'w')
            f.write( '"' + prog_openssl_fullpath + '"' + ' ' + cmd )
            f.close()
            #os.close(fileno_serial_number_cert)
            os.startfile( fname_serial_number_cert_bat )
        else:
            args = tuple( cmd.split(' ') )
            input, output = exec_command_pipe(prog_openssl_fullpath, *args)
            input.close()
            output.close()
        fserial_number_cert = file( fname_serial_number_cert, "r" )
        max = 3
        cont = 1
        while True:
            time.sleep(1)
            number_cert_str = fserial_number_cert.read()
            if number_cert_str or max < cont:
                break
            cont += 1
        fserial_number_cert.close()
        number_cert_str = number_cert_str.replace('serial=', '').replace('33', 'B').replace('3', '').replace('B', '3').replace(' ', '').replace('\r', '').replace('\n', '').replace('\r\n', '')
        return number_cert_str
        

    def _get_sello(self, cr=False, uid=False, ids=False, context={}):
        if not context:
            context = {}
        if os.name == "nt":
            prog_xsltproc = 'xsltproc.exe'
            prog_openssl = 'openssl.exe'
        else:
            prog_xsltproc = 'xsltproc'
            prog_openssl = 'openssl'
        
        subpath = os.path.join( tools.config["addons_path"], 'l10n_mx_facturae', 'depends_app')
        prog_openssl_fullpath = tools.find_in_path( prog_openssl ) or find_in_subpath(prog_openssl, subpath) or prog_openssl
        prog_xsltproc_fullpath = tools.find_in_path( prog_xsltproc ) or find_in_subpath(prog_xsltproc, subpath) or prog_xsltproc
        
        #if not prog_openssl_fullpath:
            #raise osv.except_osv('Warning !', 'No se ha encontrado la aplicacion requerida: %s.\n%s !'%(prog_openssl, msg2))
        #if not prog_xsltproc_fullpath:
            #raise osv.except_osv('Warning !', 'No se ha encontrado la aplicacion requerida: %s.\n%s !'%(prog_xsltproc, msg2))
        
        fname_xslt = context['fname_xslt']
        fname_xml = context['fname_xml']
        fname_cer = context['fname_cer']
        fname_key = context['fname_key']
        fname_sign = context['fname_sign']
        fecha = context['fecha']
        fsign = file( fname_sign, "w" )
        fsign.close()
        #fecha_2 = time.strftime('%Y-%m-%d %H:%M:%S', time.strptime(fecha, '%Y-%m-%dT%H:%M:%S'))
        #print "fecha_2",fecha_2
        year = float( time.strftime('%Y', time.strptime(fecha, '%Y-%m-%dT%H:%M:%S')) )
        if year >= 2011:
            encrypt = "sha1"
        if year <= 2010:
            encrypt = "md5"
        cmd = '"%s" "%s" | "%s" dgst -%s -sign "%s" | "%s" enc -base64 -A > "%s"'%( fname_xslt, fname_xml, \
            prog_openssl_fullpath, encrypt, fname_key, prog_openssl_fullpath, fname_sign)
        if os.name == "nt":
            (fileno_cmd, fname_cmd) = tempfile.mkstemp('.cmd', 'openerp_' + ('cmd' or '') + '__facturae__' )
            f = open(fname_cmd, 'w')
            f.write( '"' + prog_xsltproc_fullpath + '"' + ' ' + cmd )
            f.close()
            os.close(fileno_cmd)
            os.startfile( fname_cmd )
        else:
            args = tuple( cmd.split(' ') )
            input, output = exec_command_pipe(prog_xsltproc, *args)
            input.close()
            output.close()
        fsign = file( fname_sign, "r" )
        max = 3
        cont = 1
        while True:
            time.sleep(1)
            sign_str = fsign.read()
            if sign_str or max < cont:
                break
            cont += 1
        fsign.close()
        return sign_str
    
    def _xml2cad_orig(self, cr=False, uid=False, ids=False, context={}):
        if not context:
            context = {}
        if os.name == "nt":
            prog_xsltproc = 'xsltproc.exe'
        else:
            prog_xsltproc = 'xsltproc'
        
        subpath = os.path.join( tools.config["addons_path"], 'l10n_mx_facturae', 'depends_app')
        prog_xsltproc_fullpath = tools.find_in_path( prog_xsltproc ) or find_in_subpath(prog_xsltproc, subpath) or prog_xsltproc
        
        fname_xslt = context['fname_xslt']
        fname_xml = context['fname_xml']
        (fileno_cad_orig, fname_cad_orig) = tempfile.mkstemp('.cmd', 'openerp_' + ('cad_orig' or '') + '__facturae__' )
        cmd = '"%s" "%s" >"%s"'%( fname_xslt, fname_xml, fname_cad_orig )
        os.close(fileno_cad_orig)
        
        if os.name == "nt":
            (fileno_cmd, fname_cmd) = tempfile.mkstemp('.cmd', 'openerp_' + ('cmd_cad_orig' or '') + '__facturae__' )
            f = open(fname_cmd, 'w')
            f.write( '"' + prog_xsltproc_fullpath + '"' + ' ' + cmd )
            f.close()
            os.close(fileno_cmd)
            os.startfile( fname_cmd )
        else:
            args = tuple( cmd.split(' ') )
            input, output = exec_command_pipe(prog_xsltproc, *args)
            input.close()
            output.close()
        fcad_orig = file( fname_cad_orig, "r" )
        max = 3
        cont = 1
        cad_orig_str = ""
        while True:
            time.sleep(1)
            cad_orig_str = fcad_orig.read()
            if cad_orig_str or max < cont:
                break
            cont += 1
        fcad_orig.close()
        return fname_cad_orig, cad_orig_str
        
        """
        
        txt_str = ""
        fname_xml = context.get('fname_xml', '')
        fname_txt = context.get('fname_txt', '') or (fname_xml and fname_xml + '.txt' or '')
        fname_xslt = context['fname_xslt']
        if fname_xml:
            styledoc = libxml2.parseFile(fname_xslt)
            style = libxslt.parseStylesheetDoc(styledoc)
            doc = libxml2.parseFile(fname_xml)
            result = style.applyStylesheet(doc, None)
            #print "result",result
            style.saveResultToFilename(fname_txt, result, 0)
            style.freeStylesheet()
            doc.freeDoc()
            result.freeDoc()
            txt_str = open(fname_txt, "r").read()
        return fname_txt, txt_str
        """
    """
    def _get_certificate_components(self, cr=False, uid=False, ids=False, context={}):
        if not context:
            context = {}
        fname_cer = context['fname_cer']
        fcer = open(fname_cer, "r")
        pem = fcer.read()
        cer = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, pem)
        components_dict = dict( cer.get_subject().get_components() )
        return components_dict
    """
    def _get_certificate_str( self, fname_cer_pem = ""):
        fcer = open( fname_cer_pem, "r")
        lines = fcer.readlines()
        fcer.close()
        cer_str = ""
        loading = False
        for line in lines:
            if 'END CERTIFICATE' in line:
                loading = False
            if loading:
                cer_str += line
            if 'BEGIN CERTIFICATE' in line:
                loading = True
        return cer_str
    
    def _get_md5_cad_orig(self, cadorig_str, fname_cadorig_digest):
        cadorig_digest = hashlib.md5(cadorig_str).hexdigest()
        open(fname_cadorig_digest, "w").write(cadorig_digest)
        return cadorig_digest, fname_cadorig_digest
    
    def _get_facturae_invoice_dict_data(self, cr, uid, ids, context={}):
        invoices = self.browse(cr, uid, ids, context=context)
        invoice_datas = []
        invoice_data_parents = []
        #'type': fields.selection([
            #('out_invoice','Customer Invoice'),
            #('in_invoice','Supplier Invoice'),
            #('out_refund','Customer Refund'),
            #('in_refund','Supplier Refund'),
            #],'Type', readonly=True, select=True),
        for invoice in invoices:
            invoice_data_parent = {}
            if invoice.type == 'out_invoice':
                tipoComprobante = 'ingreso'
            elif invoice.type == 'out_refund':
                tipoComprobante = 'egreso'
            else:
                raise osv.except_osv('Warning !', 'Solo se puede emitir factura electronica a clientes.!')
            #Inicia seccion: Comprobante
            invoice_data_parent['Comprobante'] = {}
            #default data
            invoice_data_parent['Comprobante'].update({
                'xmlns': "http://www.sat.gob.mx/cfd/2",
                'xmlns:xsi': "http://www.w3.org/2001/XMLSchema-instance",
                    'xsi:schemaLocation': "http://www.sat.gob.mx/cfd/2 http://www.sat.gob.mx/sitio_internet/cfd/2/cfdv2.xsd",
                    'version': "2.0",
            })
            invoice_data_parent['Comprobante'].update({
                'folio': invoice.number,
                'fecha': invoice.date_invoice and \
                    #time.strftime('%d/%m/%y', time.strptime(invoice.date_invoice, '%Y-%m-%d')) \
                    time.strftime('%Y-%m-%dT%H:%M:%S', time.strptime(invoice.date_invoice, '%Y-%m-%d %H:%M:%S'))
                    or '',
                'tipoDeComprobante': tipoComprobante,
                'formaDePago': u'Pago en una sola exhibición',
                'noCertificado': '@',
                'sello': '@',
                'certificado': '@',
                'subTotal': invoice.amount_untaxed,
                'descuento': "0",#Add field general
                'total': invoice.amount_total,
            })
            folio_data = self._get_folio(cr, uid, [invoice.id], context=context)
            invoice_data_parent['Comprobante'].update({
                'anoAprobacion': folio_data['anoAprobacion'],
                'noAprobacion': folio_data['noAprobacion'],
                'serie': folio_data['serie'],
            })
            #Termina seccion: Comprobante
            #Inicia seccion: Emisor
            partner_obj = self.pool.get('res.partner')
            partner = invoice.company_id and invoice.company_id.partner_id and invoice.company_id.partner_id or False
            partner_parent = (invoice.company_id and invoice.company_id.parent_id and invoice.company_id.parent_id.partner_id) or (invoice.company_id.partner_id and invoice.company_id.partner_id) or False
            
            address_invoice_id = partner_obj.address_get(cr, uid, [partner.id], ['invoice'])['invoice']
            address_invoice_parent_id = partner_obj.address_get(cr, uid, [partner_parent.id], ['invoice'])['invoice']
            
            if not address_invoice_id:
                raise osv.except_osv('Warning !', 'No se tiene definido los datos de facturacion del partner [%s].\n%s !'%(partner.name, msg2))
            
            address_invoice = self.pool.get('res.partner.address').browse(cr, uid, address_invoice_id, context)
            address_invoice_parent = self.pool.get('res.partner.address').browse(cr, uid, address_invoice_parent_id, context)
            
            if not partner.vat:
                raise osv.except_osv('Warning !', 'No se tiene definido el RFC del partner [%s].\n%s !'%(partner.name, msg2))
            
            invoice_data = invoice_data_parent['Comprobante']
            invoice_data['Emisor'] = {}
            invoice_data['Emisor'].update({
                'rfc': (partner_parent.vat or '').replace('-', ' ').replace(' ',''),
                'nombre': address_invoice_parent.name or partner_parent.name or '',
                #Obtener domicilio dinamicamente
                #virtual_invoice.append( (invoice.company_id and invoice.company_id.partner_id and invoice.company_id.partner_id.vat or '').replac
                
                'DomicilioFiscal': {
                    'calle': address_invoice_parent.street and address_invoice_parent.street.replace('\n\r', ' ').replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ') or '',
                    #'noExterior': 'No Exterior',
                    'colonia':  address_invoice_parent.street2 and address_invoice_parent.street2.replace('\n\r', ' ').replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ') or '' ,
                    'localidad': address_invoice_parent.city and address_invoice_parent.city.replace('\n\r', ' ').replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ') or '',
                    'municipio': address_invoice_parent.city and address_invoice_parent.city.replace('\n\r', ' ').replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ') or '',
                    'estado': address_invoice_parent.state_id and address_invoice_parent.state_id.name and address_invoice_parent.state_id.name.replace('\n\r', ' ').replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ') or '' ,
                    'pais': address_invoice_parent.country_id and address_invoice_parent.country_id.name and address_invoice_parent.country_id.name.replace('\n\r', ' ').replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ')or '',
                    'codigoPostal': address_invoice_parent.zip and address_invoice_parent.zip.replace('\n\r', ' ').replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ') or '',
                },
                'ExpedidoEn': {
                    'calle': address_invoice.street and address_invoice.street.replace('\n\r', ' ').replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ') or '',
                    #'noExterior': 'No Exterior',
                    'colonia':  address_invoice.street2 and address_invoice.street2.replace('\n\r', ' ').replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ') or '' ,
                    'localidad': address_invoice.city and address_invoice.city.replace('\n\r', ' ').replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ') or '',
                    'municipio': address_invoice.city and address_invoice.city.replace('\n\r', ' ').replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ') or '',
                    'estado': address_invoice.state_id and address_invoice.state_id.name and address_invoice.state_id.name.replace('\n\r', ' ').replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ') or '' ,
                    'pais': address_invoice.country_id and address_invoice.country_id.name and address_invoice.country_id.name.replace('\n\r', ' ').replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ')or '',
                    'codigoPostal': address_invoice.zip and address_invoice.zip.replace('\n\r', ' ').replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ') or '',
                },
            })
            #Termina seccion: Emisor
            #Inicia seccion: Receptor
            if not invoice.partner_id.vat:
                raise osv.except_osv('Warning !', 'No se tiene definido el RFC del partner [%s].\n%s !'%(invoice.partner_id.name, msg2))
            invoice_data['Receptor'] = {}
            invoice_data['Receptor'].update({
                'rfc': (invoice.partner_id.vat or '').replace('-', ' ').replace(' ',''),
                'nombre': (invoice.address_invoice_id.name or invoice.partner_id.name or ''),
                'Domicilio': {
                    'calle': invoice.address_invoice_id.street and invoice.address_invoice_id.street.replace('\n\r', ' ').replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ') or '',
                    #'noExterior': 'No Exterior',
                    'colonia':  invoice.address_invoice_id.street2 and invoice.address_invoice_id.street2.replace('\n\r', ' ').replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ') or '' ,
                    'localidad': invoice.address_invoice_id.city and invoice.address_invoice_id.city.replace('\n\r', ' ').replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ') or '',
                    'municipio': invoice.address_invoice_id.city and invoice.address_invoice_id.city.replace('\n\r', ' ').replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ') or '',
                    'estado': invoice.address_invoice_id.state_id and invoice.address_invoice_id.state_id.name and invoice.address_invoice_id.state_id.name.replace('\n\r', ' ').replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ') or '' ,
                    'pais': invoice.address_invoice_id.country_id and invoice.address_invoice_id.country_id.name and invoice.address_invoice_id.country_id.name.replace('\n\r', ' ').replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ')or '',
                    'codigoPostal': invoice.address_invoice_id.zip and invoice.address_invoice_id.zip.replace('\n\r', ' ').replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ') or '',
                },
            })
            #Termina seccion: Receptor
            #Inicia seccion: Conceptos
            invoice_data['Conceptos'] = []
            for line in invoice.invoice_line:
                concepto = {
                    'cantidad': "%.2f"%( line.quantity or 0.0),
                    'descripcion': line.name or '',
                    'valorUnitario': "%.2f"%( line.price_unit or 0.0),
                    'importe': "%.2f"%( line.price_subtotal or 0.0),#round(line.price_unit *(1-(line.discount/100)),2) or 0.00),#Calc: iva, disc, qty
                    ##Falta agregar discount
                    ##Falta agregar codigo del producto
                }
                unidad = line.uos_id and line.uos_id.name or ''
                if unidad:
                    concepto.update({'unidad': unidad})
                product_code = line.product_id and line.product_id.default_code or ''
                if product_code:
                    concepto.update({'noIdentificacion': product_code})
                invoice_data['Conceptos'].append( {'Concepto': concepto} )
            #Termina seccion: Conceptos
            #Inicia seccion: impuestos
            invoice_data['Impuestos'] = {}
            invoice_data['Impuestos'].update({
                #'totalImpuestosTrasladados': "%.2f"%( invoice.amount_tax or 0.0),
            })
            invoice_data['Impuestos'].update({
                #'totalImpuestosRetenidos': "%.2f"%( invoice.amount_tax or 0.0 )
            })
            
            invoice_data_impuestos = invoice_data['Impuestos']
            invoice_data_impuestos['Traslados'] = []
            #invoice_data_impuestos['Retenciones'] = []
            
            tax_names = []
            totalImpuestosTrasladados = 0
            totalImpuestosRetenidos = 0
            for line_tax_id in invoice.tax_line:
                #tax_name = line_tax_id.name.split(' - ')[0]
                tax_name = line_tax_id.name.lower().replace('.','').replace(' ', '').replace('-', '')
                if 'iva' in tax_name:
                    tax_name = 'IVA'
                elif 'isr' in tax_name:
                    tax_name = 'ISR'
                elif 'ieps' in tax_name:
                    tax_name = 'IEPS'
                tax_names.append( tax_name )
                line_tax_id_amount = abs( line_tax_id.amount or 0.0 )
                tasa = line_tax_id_amount and invoice.amount_untaxed and line_tax_id_amount * 100 / invoice.amount_untaxed or 0.0
                
                if line_tax_id.amount > 0:
                    impuesto_list = invoice_data_impuestos['Traslados']
                    impuesto_str = 'Traslado'
                    totalImpuestosTrasladados += line_tax_id_amount
                else:
                    #impuesto_list = invoice_data_impuestos['Retenciones']
                    impuesto_list = invoice_data_impuestos.setdefault('Retenciones', [])
                    impuesto_str = 'Retencion'
                    totalImpuestosRetenidos += line_tax_id_amount
                impuesto_dict = {impuesto_str: 
                    {
                        'impuesto': tax_name,
                        'importe': "%.2f"%( line_tax_id_amount ),
                    }
                }
                if line_tax_id.amount > 0:
                    impuesto_dict[impuesto_str].update({'tasa': "%.2f"%( tasa )})
                impuesto_list.append( impuesto_dict )
            
            invoice_data['Impuestos'].update({
                'totalImpuestosTrasladados': "%.2f"%( totalImpuestosTrasladados ),
            })
            if totalImpuestosRetenidos:
                invoice_data['Impuestos'].update({
                    'totalImpuestosRetenidos': "%.2f"%( totalImpuestosRetenidos )
                })
                
            tax_requireds = ['IVA', 'IEPS']
            for tax_required in tax_requireds:
                if tax_required in tax_names:
                    continue
                invoice_data_impuestos['Traslados'].append( {'Traslado': {
                    'impuesto': tax_required,
                    'tasa': "%.2f"%( 0.0 ),
                    'importe': "%.2f"%( 0.0 ),
                }} )
            #Termina seccion: impuestos
            invoice_data_parents.append( invoice_data_parent )
            invoice_data_parent['state'] = invoice.state
            invoice_data_parent['invoice_id'] = invoice.id
            invoice_data_parent['type'] = invoice.type
            invoice_data_parent['date_invoice'] = invoice.date_invoice
        return invoice_data_parents
account_invoice()