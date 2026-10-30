import datetime as dt, io, json, os, pathlib, re, subprocess, sys, time, urllib.request
import chess, chess.pgn
ROOT=pathlib.Path(__file__).resolve().parent
EXE=ROOT/'rom_console'; FILE=ROOT/'status.json'; RESULTS=ROOT/'results.json'
IDS=['4xLfA0En','KicQp8vU','fIfq3LZR','z5vB3TII','k6kRDIK1','L1eiMWmn','PpL7KEKy','y5VebmDO','RJQS7j5G','KPtKmETT','Cy4v4dlS','HjGgG3Dn','lBdYC3vM','ZcyZ5DVD','44kFiZlc','fxpx4587','LAt4RZVy','KU6tPNfj','MC5fBpLs','InyVvVo7','Pap9LVsX','zTCW809p','Tow5byBK']
BASE={'Easy':(104,17,14,222),'Intermediate':(17,11,0,762),'Advanced':(12,11,3,144)}
PIECES={'p':'b','n':'c','b':'d','r':'e','q':'f','k':'g'}
CODES={'.':7,'P':1,'N':2,'B':3,'R':4,'Q':5,'K':6,'k':8,'q':9,'r':10,'b':11,'n':12,'p':13}
def now():return dt.datetime.now(dt.timezone.utc).isoformat()
def chapter(n):return 'Easy' if n<=222 else ('Intermediate' if n<=984 else 'Advanced')
def read_rows():
 try:return json.loads(RESULTS.read_text(encoding='utf8'))
 except (OSError,ValueError):return {}
def status(rows,active=None,running=True):
 chapters={};totals={'solved':0,'failed':0,'technical':0}
 for name,(sol,fail,tech,count) in BASE.items():
  vals={'solved':sol,'failed':fail,'technical':tech}
  for n,v in rows.items():
   if chapter(int(n))==name and v['status'] in vals:vals[v['status']]+=1
  vals['total']=count;vals['graded']=vals['solved']+vals['failed'];vals['observed']=vals['graded']+vals['technical']
  vals['pending']=max(0,count-vals['observed'])
  vals['solved_rate']=round(100*vals['solved']/vals['graded'],2) if vals['graded'] else None
  chapters[name]=vals
  for k in totals:totals[k]+=vals[k]
 totals['total']=1128;totals['graded']=totals['solved']+totals['failed']
 totals['observed']=totals['graded']+totals['technical']
 totals['pending']=1128-totals['observed']
 totals['solved_rate']=round(100*totals['solved']/totals['graded'],2)
 payload={'schema':2,'generated_utc':now(),'feed_relay_connected':True,'source_machine':'GitHub Actions Linux (not PC)',
  'last_result_utc':max((r['finished_at'] for r in rows.values()),default='2026-10-29T15:35:29+00:00'),
  'chapters':chapters,'totals':totals,'active_search_processes':1 if active else 0,'worker':{'active':running,'current_puzzle':active},
  'batches':[{'name':'GitHub-hosted Mephisto A8','running':running,'active_searches':1 if active else 0}],
  'contains_solutions':False,'legacy_aggregate_reconciliation_pending':True}
 FILE.write_text(json.dumps(payload,indent=2),encoding='utf8')
def push(rows,active=None,running=True):
 status(rows,active,running)
 subprocess.run(['git','add','status.json','results.json'],check=True)
 subprocess.run(['git','commit','-m','Woodpecker A8 spoiler-free checkpoint'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 p=subprocess.run(['git','push','origin','HEAD:main'],capture_output=True,text=True,timeout=90)
 if p.returncode:print('CHECKPOINT_PUSH_ERROR',p.stderr[-250:],flush=True)
def positions():
 out={}
 for part,id in enumerate(IDS,1):
  try:
   req=urllib.request.Request('https://lichess.org/api/study/'+id+'.pgn',headers={'User-Agent':'Woodpecker-Mephisto-A8/1.0'})
   with urllib.request.urlopen(req,timeout=35) as response:s=response.read().decode('utf-8-sig')
  except Exception as e:
   print('STUDY_ERROR',part,str(e)[:100],flush=True);continue
  buffer=io.StringIO(s)
  while True:
   try:g=chess.pgn.read_game(buffer)
   except Exception as e:print('PARSE_ERROR',part,type(e).__name__,flush=True);break
   if g is None:break
   m=re.search(r'(?:Puzzle\s*no\.?|Exercise)\s*(\d+)',g.headers.get('ChapterName',''),re.I)
   if not m:continue
   n=int(m.group(1))
   if not (151<=n<=222 or 251<=n<=984 or 1011<=n<=1128):continue
   try:
    b=chess.Board(g.headers['FEN']);move=next(g.mainline_moves())
    if move not in b.legal_moves:continue
    out[n]=(b,move)
   except (KeyError,ValueError,StopIteration):pass
  print('STUDY_LOADED',part,len(out),flush=True)
 return out
def predecessor(b):
 if b.turn:return b.copy(stack=False),None
 if b.castling_rights or b.ep_square:raise ValueError('requires_special_rights_history')
 for to,piece in sorted(b.piece_map().items()):
  if piece.color!=chess.WHITE:continue
  sources=[to-8] if piece.piece_type==chess.PAWN else chess.SQUARES
  for frm in sources:
   if not 0<=frm<64 or b.piece_at(frm):continue
   prev=b.copy(stack=False);prev.remove_piece_at(to);prev.set_piece_at(frm,piece)
   prev.turn=True;prev.castling_rights=0;prev.ep_square=None
   mv=chess.Move(frm,to)
   if mv not in prev.legal_moves:continue
   check=prev.copy(stack=False);check.push(mv)
   if check.board_fen()==b.board_fen() and check.ep_square==b.ep_square:return prev,mv.uci()
 raise ValueError('no_safe_predecessor')
def cmds(b):
 if b.castling_rights or b.ep_square:raise ValueError('requires_special_rights_history')
 prev,last=predecessor(b)
 out=['boot','level a8']
 for rank,side in ((1,'WS'),(2,'WS'),(7,'SW'),(8,'SW')):
  for letter in 'abcdefgh':out+=['key '+side,'key a','key '+letter,'key '+str(rank),'key ENT']
 for sq,p in sorted(prev.piece_map().items()):
  q=chess.square_name(sq)
  out+=['key '+('WS' if p.color else 'SW'),'key '+PIECES[p.symbol().lower()],'key '+q[0],'key '+q[1],'key ENT']
 out+=['key WS','key ENT']
 if last:out+=['key '+x for x in last]+['key ENT']
 return '\n'.join(out+['dump','search','quit'])+'\n'
def verify(board,boardhex):
 try:data=bytes.fromhex(boardhex)
 except ValueError:return False
 if len(data)!=64:return False
 for sq in chess.SQUARES:
  p=board.piece_at(sq);s=p.symbol() if p else '.'
  if not board.turn and s!='.':s=s.swapcase()
  if data[sq if board.turn else sq^56]!=CODES[s]:return False
 return True
def attempt(board,solution):
 q=subprocess.run([str(EXE)],input=cmds(board),text=True,capture_output=True)
 if q.returncode:raise RuntimeError('ROM exit '+str(q.returncode))
 snap=next((json.loads(s) for s in q.stdout.splitlines() if s.startswith('{')),None)
 if not snap or not verify(board,snap.get('board','')):raise ValueError('ROM position mismatch')
 candidates=[s.split()[1] for s in q.stdout.splitlines() if s.startswith('bestmove ')]
 if len(candidates)!=1:raise RuntimeError('no naturally returned ROM move')
 move=chess.Move.from_uci(candidates[0])
 if move not in board.legal_moves:raise ValueError('ROM move is illegal')
 return move==solution
def main():
 rows=read_rows();data=positions()
 if not data:raise RuntimeError('No valid Lichess puzzles found; refusing to manufacture results')
 ids=[n for n in sorted(data) if str(n) not in rows]
 groups={c:[i for i in ids if chapter(i)==c] for c in BASE}
 queue=[]
 while any(groups.values()):
  for c in groups:
   if groups[c]:queue.append(groups[c].pop(0))
 print('QUEUED',len(queue),'puzzles',flush=True)
 push(rows,active=None,running=True)
 for n in queue:
  board,solution=data[n]
  print('SEARCH_START',n,now(),flush=True)
  status(rows,active=n)
  try:
   status_name='solved' if attempt(board,solution) else 'failed';reason=None
  except Exception as e:
   status_name='technical';reason=type(e).__name__+':'+str(e)[:100]
  rows[str(n)]={'status':status_name,'finished_at':now()}
  if reason:rows[str(n)]['reason']=reason
  RESULTS.write_text(json.dumps(rows,indent=2),encoding='utf8')
  push(rows,running=True)
  print('SEARCH_DONE',n,status_name,flush=True)
 status(rows,running=False);push(rows,running=False)
if __name__=='__main__':main()
