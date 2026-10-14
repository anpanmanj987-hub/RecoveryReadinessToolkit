const demoRef = ref => ({ref});
const demoAll = (...refs) => ({all:refs.map(demoRef)});
const demoResource = (id,label,category,initial,owner,notes='') => ({id,label,kind:'resource',category,initial,owner,notes,evidence:{status:'not-tested'}});
const demoRoute = (id,label,...refs) => ({id,label,requires:demoAll(...refs)});
const demoAction = (id,label,category,routes,owner,notes='') => ({id,label,kind:'action',category,routes,owner,notes,evidence:{status:'not-tested'}});
export const DEMO = {
  schemaVersion:1,name:'架空例 / Identity & PAM Recovery',
  description:'製品の実仕様ではなく、循環する復旧条件を説明するための架空構成です。実環境の証跡・資格情報は含みません。IdP停止時、資格情報はPAM内、手順書はSSO配下。独立手段の有無で開始可否が変わります。',
  nodes:[
    demoResource('idp-health','通常認証サービス','identity','available','認証チーム','障害シナリオでは停止したまま。復旧後の利用は「認証基盤の復旧操作」を別経路として表現。'),
    demoResource('maintenance-net','独立した保守回線','network','available','NWチーム','モデル上の申告。回線の共通障害要因は別途点検。'),
    demoResource('admin-device','管理用端末','system','available','運用チーム'),
    demoResource('oncall','当番・承認者の確保','people','available','運用責任者'),
    demoResource('offline-kit','独立した緊急認証手段','credential','unavailable','認証チーム','鍵・パスワードそのものは保存しない。強い認証、独立した利用条件、承認・監査を備えた手段を別途設計。'),
    demoResource('offline-runbook','オフライン手順書','document','unavailable','BCPチーム','実行に必要な手順が、停止する認証に依存せず参照可能か。'),
    demoResource('backup-media','復元用バックアップ','system','available','バックアップ担当','ファイルの存在だけで整合性・復元成功を保証するものではない。'),
    demoResource('hotline','独立した緊急連絡先','people','unknown','BCPチーム','当該障害条件でも連絡可能か未確認。'),
    demoAction('cloud-login','管理者の認証','identity',[
      demoRoute('normal','通常認証','idp-health','maintenance-net','admin-device'),
      demoRoute('restored','復旧した認証基盤を使う','recover-idp','maintenance-net','admin-device')
    ],'認証チーム'),
    demoAction('pam-login','PAMにログイン','identity',[
      demoRoute('normal','SSO経由','cloud-login','maintenance-net'),
      demoRoute('independent','独立した緊急アクセス経由','offline-kit','maintenance-net','admin-device','oncall')
    ],'PAMチーム'),
    demoAction('recovery-secret','復旧用資格情報の取得','credential',[demoRoute('vault','PAM内から取得','pam-login')],'PAMチーム','取得できる条件のみ記録。秘密値は一切入力しない。'),
    demoAction('read-runbook','復旧手順書の参照','document',[
      demoRoute('online','SSO配下のオンライン版','cloud-login'),
      demoRoute('offline','独立したオフライン版','offline-runbook')
    ],'BCPチーム'),
    demoAction('recover-idp','認証基盤の復旧操作','system',[demoRoute('recovery','資格情報・手順・作業環境が必要','recovery-secret','read-runbook','maintenance-net','admin-device','oncall')],'認証チーム'),
    demoAction('backup-console','復元コンソールへのアクセス','system',[demoRoute('pam','PAMと手順書が必要','pam-login','read-runbook')],'バックアップ担当'),
    {...demoAction('goal-identity','認証復旧の作業を開始','system',[demoRoute('start','復旧操作の前提が成立','recover-idp')],'認証チーム'),kind:'goal',systemId:'DEMO-ID-01'},
    {...demoAction('goal-restore','業務データの復元を開始','system',[demoRoute('start','コンソール・媒体・当番が必要','backup-console','backup-media','oncall')],'バックアップ担当'),kind:'goal',systemId:'DEMO-APP-01'},
    {...demoAction('goal-notify','障害時の連絡を開始','people',[demoRoute('contact','独立した連絡先と当番','hotline','oncall')],'BCPチーム'),kind:'goal'}
  ],
  scenarios:[
    {id:'identity-outage',name:'認証基盤停止',description:'通常認証サービスが利用できない状態。代替アクセスの入口と手順書の所在を確認する。',unavailable:['idp-health'],unknown:[]},
    {id:'baseline',name:'通常時の前提確認',description:'強制停止なし。利用可能と申告した初期条件を前提にする。',unavailable:[],unknown:[]},
    {id:'network-outage',name:'保守回線停止',description:'保守回線をシナリオ全体で停止させる。別回線を使う場合は別条件として追加する。',unavailable:['maintenance-net'],unknown:[]},
    {id:'compound-outage',name:'認証＋保守回線停止',description:'共通障害で認証と保守経路の両方が失われた場合。',unavailable:['idp-health','maintenance-net'],unknown:[]}
  ]
};
export function improvedDemo() {
  const model=structuredClone(DEMO);
  for(const id of ['offline-kit','offline-runbook'])model.nodes.find(n=>n.id===id).initial='available';
  model.name='架空例 / Independent Recovery Path';
  return model;
}
export function emptyModel() {
  return {schemaVersion:1,name:'新しい復旧モデル',description:'',nodes:[{id:'goal-1',label:'最初の復旧目標',kind:'goal',category:'system',routes:[],owner:'',evidence:{status:'not-tested'}}],scenarios:[{id:'baseline',name:'通常時の前提確認',unavailable:[],unknown:[]}]};
}
