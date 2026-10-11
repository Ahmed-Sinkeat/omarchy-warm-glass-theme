#include <QGuiApplication>
#include <QFontDatabase>
#include <QTextLayout>
#include <QGlyphRun>
#include <QFile>
#include <QJsonDocument>
#include <QJsonObject>
#include <cstdio>
#include <QQmlEngine>
#include <QQmlComponent>
#include <QQmlContext>
#include <QVariant>
int main(int argc,char**argv){
 QGuiApplication app(argc,argv);
 if(argc!=5 || QFontDatabase::addApplicationFont(argv[1])<0 || QFontDatabase::addApplicationFont(argv[2])<0)return 2;
 QFile file(argv[3]);if(!file.open(QIODevice::ReadOnly))return 2;
 const auto names=QJsonDocument::fromJson(file.readAll()).object();
 QQmlEngine engine;
 auto qmlFont=[&](const char* family){
  engine.rootContext()->setContextProperty("familyUnderTest",QString::fromUtf8(family));
  QQmlComponent component(&engine);
  component.setData("import QtQuick\nText { font.family: familyUnderTest; font.pixelSize: 16 }",QUrl());
  auto object=component.create();
  if(!object){fprintf(stderr,"FAIL: QML font component\n");std::exit(2);}
  QFont font=object->property("font").value<QFont>();delete object;return font;
 };
 QFont f=qmlFont(argv[4]);
 for(auto it=names.begin();it!=names.end();++it){
  QTextLayout layout(it.key(),f);layout.beginLayout();layout.createLine();layout.endLayout();
  const auto runs=layout.glyphRuns();
  if(runs.size()!=1 || (runs[0].rawFont().familyName()!="Warm Glass Icons" && !(it.key().toUcs4()[0]<0xe000 && runs[0].rawFont().familyName()=="Adwaita Sans")) || runs[0].glyphIndexes().contains(0)){
   fprintf(stderr,"FAIL: %s rendered by %s\n",it.value().toString().toUtf8().constData(),runs.empty()?"none":runs[0].rawFont().familyName().toUtf8().constData());return 1;
  }
 }
 QTextLayout normal("1900 RPM 50%",f);normal.beginLayout();normal.createLine();normal.endLayout();
 for(const auto &run:normal.glyphRuns())if(run.rawFont().familyName()!="Adwaita Sans" || run.glyphIndexes().contains(0))return 1;
 QTextLayout arabic(QString::fromUtf8("العربية 🐧"),f);arabic.beginLayout();arabic.createLine();arabic.endLayout();
 for(const auto &run:arabic.glyphRuns())if(run.glyphIndexes().contains(0))return 1;
 printf("PASS: Actual QML font selection covers %d symbols; private-use icons use Lucide, text uses Adwaita Sans; Arabic and emoji retained\n",int(names.size()));
}
