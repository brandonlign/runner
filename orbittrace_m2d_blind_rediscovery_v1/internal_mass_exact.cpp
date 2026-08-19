#include <bits/stdc++.h>
using namespace std;

struct LCT {
    struct N { int ch[2]{0,0}, p=0; bool rev=false; int val=INT_MAX, mn=INT_MAX, mnid=0; };
    vector<N> t;
    LCT(int n=0): t(n+1) { for(int i=1;i<=n;i++){t[i].mnid=i;} }
    void resetNode(int x,int val){ t[x]=N(); t[x].val=val; t[x].mn=val; t[x].mnid=x; }
    bool isRoot(int x){ int p=t[x].p; return p==0 || (t[p].ch[0]!=x && t[p].ch[1]!=x); }
    void pull(int x){ t[x].mn=t[x].val; t[x].mnid=x; for(int d=0;d<2;d++){ int c=t[x].ch[d]; if(c && t[c].mn < t[x].mn){ t[x].mn=t[c].mn; t[x].mnid=t[c].mnid; } } }
    void applyRev(int x){ if(!x)return; swap(t[x].ch[0],t[x].ch[1]); t[x].rev=!t[x].rev; }
    void push(int x){ if(t[x].rev){ applyRev(t[x].ch[0]); applyRev(t[x].ch[1]); t[x].rev=false; } }
    void pushPath(int x){ static vector<int> st; st.clear(); int y=x; st.push_back(y); while(!isRoot(y)){ y=t[y].p; st.push_back(y);} for(auto it=st.rbegin();it!=st.rend();++it) push(*it); }
    void rotate(int x){ int p=t[x].p,g=t[p].p; int dx=(t[p].ch[1]==x); int b=t[x].ch[dx^1]; if(!isRoot(p)) t[g].ch[t[g].ch[1]==p]=x; t[x].p=g; t[x].ch[dx^1]=p; t[p].p=x; t[p].ch[dx]=b; if(b)t[b].p=p; pull(p); pull(x); }
    void splay(int x){ pushPath(x); while(!isRoot(x)){ int p=t[x].p,g=t[p].p; if(!isRoot(p)){ bool zigzig=(t[p].ch[1]==x)==(t[g].ch[1]==p); rotate(zigzig?p:x);} rotate(x);} pull(x); }
    void access(int x){ int last=0; for(int y=x;y;y=t[y].p){ splay(y); t[y].ch[1]=last; pull(y); last=y;} splay(x); }
    void makeRoot(int x){ access(x); applyRev(x); }
    int findRoot(int x){ access(x); push(x); while(t[x].ch[0]){ x=t[x].ch[0]; push(x);} splay(x); return x; }
    bool connected(int a,int b){ if(a==b)return true; makeRoot(a); return findRoot(b)==a; }
    void link(int a,int b){ makeRoot(a); if(findRoot(b)!=a) t[a].p=b; }
    bool cut(int a,int b){ makeRoot(a); access(b); if(t[b].ch[0]!=a || t[a].ch[1]) return false; t[b].ch[0]=0; t[a].p=0; pull(b); return true; }
    int queryMinId(int a,int b){ makeRoot(a); access(b); return t[b].mnid; }
};

struct DSU {
    vector<int> p,sz; vector<char> act,bad; long long good=0;
    DSU(int n):p(n),sz(n,0),act(n,0),bad(n,0){iota(p.begin(),p.end(),0);}
    int f(int x){ while(p[x]!=x){ p[x]=p[p[x]]; x=p[x]; } return x; }
    long long q(int r){ return (!bad[r] && sz[r]>=4)?sz[r]:0; }
    void activate(int x){ if(act[x])return; act[x]=1;p[x]=x;sz[x]=1;bad[x]=0; }
    void unite(int a,int b){ if(!act[a]||!act[b]) return; a=f(a);b=f(b);if(a==b)return;good-=q(a)+q(b); if(sz[a]<sz[b])swap(a,b);p[b]=a;sz[a]+=sz[b];bad[a]=bad[a]||bad[b];good+=q(a); }
    void markBad(int x){ if(!act[x]) return; int r=f(x); if(bad[r])return;good-=q(r);bad[r]=1;good+=q(r); }
};
struct IEdge{int u,v,a,b;}; struct XEdge{int u,a,b;};

int main(int argc,char**argv){
    if(argc<3){cerr<<"usage: exact input.bin output.tsv\n";return 2;}
    ifstream in(argv[1],ios::binary); if(!in){cerr<<"input open fail\n";return 2;}
    char magic[8];in.read(magic,8); if(string(magic,5)!="OTIM1"){cerr<<"bad magic\n";return 2;}
    uint32_t N13,N14,C; in.read((char*)&N13,4);in.read((char*)&N14,4);in.read((char*)&C,4);
    ofstream out(argv[2]); out<<setprecision(17); out<<"candidate\tn\tm\tx\tinternal_mass\touter_levels\tforest_replacements\n";
    for(uint32_t ci=0;ci<C;ci++){
        uint32_t n,m,xn;in.read((char*)&n,4);in.read((char*)&m,4);in.read((char*)&xn,4);
        vector<int>d13(n),d14(n);for(uint32_t i=0;i<n;i++){int32_t a,b;in.read((char*)&a,4);in.read((char*)&b,4);d13[i]=a;d14[i]=b;}
        vector<IEdge> es;es.reserve(m);for(uint32_t k=0;k<m;k++){uint32_t u,v;in.read((char*)&u,4);in.read((char*)&v,4); es.push_back({(int)u,(int)v,min(d13[u],d13[v]),min(d14[u],d14[v])});}
        vector<XEdge> xs;xs.reserve(xn);for(uint32_t k=0;k<xn;k++){uint32_t u;int32_t a,b;in.read((char*)&u,4);in.read((char*)&a,4);in.read((char*)&b,4); if(a>0&&b>0)xs.push_back({(int)u,(int)a,(int)b});}
        vector<int> blevels;blevels.reserve(n+xs.size());for(int z:d14)if(z>0)blevels.push_back(z);for(auto&e:xs)blevels.push_back(e.b);sort(blevels.begin(),blevels.end(),greater<int>());blevels.erase(unique(blevels.begin(),blevels.end()),blevels.end());
        sort(es.begin(),es.end(),[](auto&A,auto&B){return A.b>B.b;});
        LCT lct((int)(2*n+5)); for(uint32_t i=0;i<n;i++)lct.resetNode((int)i+1,INT_MAX);
        vector<char> edgeActive(2*n+5,0); vector<int> eu(2*n+5,-1),ev(2*n+5,-1),ewa(2*n+5,INT_MAX); int nextEdge=(int)n+1; long long replacements=0; size_t ep=0;
        auto addForestEdge=[&](const IEdge&e){ int u=e.u+1,v=e.v+1,w=e.a; if(!lct.connected(u,v)){ int id=nextEdge++; if(id>=(int)lct.t.size()){cerr<<"edge node overflow ci="<<ci<<"\n";exit(3);} lct.resetNode(id,w);eu[id]=u;ev[id]=v;ewa[id]=w;edgeActive[id]=1;lct.link(u,id);lct.link(id,v); }
            else { int id=lct.queryMinId(u,v); if(id<=(int)n){cerr<<"path min vertex ci="<<ci<<"\n";exit(3);} if(lct.t[id].val < w){ if(!lct.cut(eu[id],id)||!lct.cut(ev[id],id)){cerr<<"cut fail\n";exit(3);} edgeActive[id]=0; replacements++; lct.resetNode(id,w);eu[id]=u;ev[id]=v;ewa[id]=w;edgeActive[id]=1;lct.link(u,id);lct.link(id,v);} }
        };
        long double total=0.0L;
        for(size_t bi=0;bi<blevels.size();bi++){
            int b=blevels[bi]; while(ep<es.size() && es[ep].b>=b){ addForestEdge(es[ep]); ep++; }
            int bnext=(bi+1<blevels.size()?blevels[bi+1]:0); long double wb=(long double)(b-bnext)/(long double)N14;
            vector<int> alevels; alevels.reserve(n+xs.size());
            for(uint32_t u=0;u<n;u++) if(d14[u]>=b && d13[u]>0) alevels.push_back(d13[u]);
            for(auto &xe:xs) if(xe.b>=b && xe.a>0) alevels.push_back(xe.a);
            if(alevels.empty()) continue;
            sort(alevels.begin(),alevels.end(),greater<int>());alevels.erase(unique(alevels.begin(),alevels.end()),alevels.end());
            unordered_map<int, vector<int>> verts; verts.reserve(alevels.size()*2); for(uint32_t u=0;u<n;u++) if(d14[u]>=b && d13[u]>0) verts[d13[u]].push_back((int)u);
            unordered_map<int, vector<pair<int,int>>> fedges; fedges.reserve(alevels.size()*2); for(int id=(int)n+1;id<nextEdge;id++) if(edgeActive[id]){ int u=eu[id]-1,v=ev[id]-1; if(d14[u]>=b && d14[v]>=b) fedges[ewa[id]].push_back({u,v}); }
            unordered_map<int, vector<int>> bads; bads.reserve(alevels.size()*2); for(auto &xe:xs) if(xe.b>=b) bads[xe.a].push_back(xe.u);
            DSU dsu(n); long double inner=0.0L;
            for(size_t ai=0;ai<alevels.size();ai++){
                int a=alevels[ai]; auto itv=verts.find(a);if(itv!=verts.end())for(int u:itv->second)dsu.activate(u);
                auto ite=fedges.find(a);if(ite!=fedges.end())for(auto [u,v]:ite->second)dsu.unite(u,v);
                auto itb=bads.find(a);if(itb!=bads.end())for(int u:itb->second)dsu.markBad(u);
                int anext=(ai+1<alevels.size()?alevels[ai+1]:0); long double wa=(long double)(a-anext)/(long double)N13; inner += (long double)dsu.good * wa;
            }
            total += inner*wb;
        }
        long double score=n?total/(long double)n:0.0L;
        out<<ci<<'\t'<<n<<'\t'<<m<<'\t'<<xs.size()<<'\t'<<(double)score<<'\t'<<blevels.size()<<'\t'<<replacements<<"\n";
    }
}
