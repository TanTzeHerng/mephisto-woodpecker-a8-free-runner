#define FLAT_MEMORY
#define BATCHED
#include "mephisto_core.h"
#include <chrono>
#include <iostream>
#include <string>
#include <algorithm>
#include <iomanip>
using Clock=std::chrono::steady_clock;
static bool coordinate(const std::string&s){return s.size()==4&&s[0]>='a'&&s[0]<='h'&&s[1]>='1'&&s[1]<='8'&&s[2]>='a'&&s[2]<='h'&&s[3]>='1'&&s[3]<='8';}
static void search(Mephisto&m){
 auto start=Clock::now(); auto begin=m.cycles; std::string prior;int stable=0,idle_score=0;
 while(true){
  m.run(Mephisto::HZ/60);std::string move=m.display();
  bool idle=(m.r[m.p]>=5139&&m.r[m.p]<=5141)||m.r[m.p]==5669;
  if(coordinate(move)&&move==prior)stable++;else stable=0;
  if(idle&&coordinate(move))idle_score++;else idle_score=std::max(0,idle_score-3);
  prior=move;
  if(stable>=120&&idle_score>=120){double wall=std::chrono::duration<double>(Clock::now()-start).count();
   std::cout<<"bestmove "<<move<<"\n"<<std::flush;
   std::cerr<<std::setprecision(12)<<"emulated_seconds="<<double(m.cycles-begin)/Mephisto::HZ<<" wall_seconds="<<wall<<"\n"<<std::flush;
   return;
  }
 }
}
int main(){try{
 Mephisto m;std::string line;
 while(std::getline(std::cin,line)){
  std::istringstream in(line);std::string cmd;in>>cmd;
  if(cmd=="quit")break;
  if(cmd=="boot")m.boot();
  else if(cmd=="reset")m=Mephisto();
  else if(cmd=="level"){std::string s;in>>s;m.level(s);}
  else if(cmd=="key"){std::string s;in>>s;m.key(s);}
  else if(cmd=="move"){std::string s;in>>s;m.move(s,false);}
  else if(cmd=="dump")std::cout<<m.snapshot()<<"\n"<<std::flush;
  else if(cmd=="search"){m.key("STA");search(m);}
  else if(!cmd.empty())throw std::runtime_error("Unknown command: "+cmd);
 }
 return 0;
}catch(const std::exception&e){std::cerr<<"error: "<<e.what()<<"\n";return 1;}}