from django.db import models

# Create your models here.

class Book(models.Model):
    title = models.CharField(max_length=30)
    description = models.TextField(null=True)

class Chapter(models.Model):
    book = models.ForeignKey('Book', on_delete=models.CASCADE)
    number = models.IntegerField()

class Verse(models.Model):
    chapter = models.ForeignKey('Chapter', on_delete=models.CASCADE)
    strong_nums = models.TextField() # list of strong nums that are ids

class StrongWord(models.Model):
    strong_num = models.IntegerField()
    language = models.CharField(max_length=1) # h, g
    characters = models.CharField(max_length=60)
    strong_def = models.TextField() # HebrewStrong.xml
    bdb_def = models.TextField() # BrownDriverBriggs.xml

