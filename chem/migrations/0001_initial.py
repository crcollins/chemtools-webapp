# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'ErrorReport'
        db.create_table('chem_errorreport', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('molecule', self.gf('django.db.models.fields.CharField')(max_length=400)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('email', self.gf('django.db.models.fields.EmailField')(max_length=75)),
            ('urgency', self.gf('django.db.models.fields.IntegerField')()),
            ('message', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('chem', ['ErrorReport'])

        # Adding model 'Job'
        db.create_table('chem_job', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('molecule', self.gf('django.db.models.fields.CharField')(max_length=400)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=400)),
            ('email', self.gf('django.db.models.fields.EmailField')(max_length=75)),
            ('cluster', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('nodes', self.gf('django.db.models.fields.IntegerField')()),
            ('walltime', self.gf('django.db.models.fields.IntegerField')()),
            ('jobid', self.gf('django.db.models.fields.CharField')(max_length=400)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('started', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('ended', self.gf('django.db.models.fields.DateTimeField')(null=True)),
        ))
        db.send_create_signal('chem', ['Job'])


    def backwards(self, orm):
        # Deleting model 'ErrorReport'
        db.delete_table('chem_errorreport')

        # Deleting model 'Job'
        db.delete_table('chem_job')


    models = {
        'chem.errorreport': {
            'Meta': {'object_name': 'ErrorReport'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.TextField', [], {}),
            'molecule': ('django.db.models.fields.CharField', [], {'max_length': '400'}),
            'urgency': ('django.db.models.fields.IntegerField', [], {})
        },
        'chem.job': {
            'Meta': {'object_name': 'Job'},
            'cluster': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'ended': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'jobid': ('django.db.models.fields.CharField', [], {'max_length': '400'}),
            'molecule': ('django.db.models.fields.CharField', [], {'max_length': '400'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '400'}),
            'nodes': ('django.db.models.fields.IntegerField', [], {}),
            'started': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'walltime': ('django.db.models.fields.IntegerField', [], {})
        }
    }

    complete_apps = ['chem']