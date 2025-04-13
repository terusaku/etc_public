
```sh
aws appmesh list-virtual-routers --mesh-name ${MESH_NAME}
aws appmesh list-virtual-routers --mesh-name ${MESH_NAME} | jq -r '.virtualRouters[] | ["virtualRouter", .virtualRouterName] | @csv' > ~/Downloads/mesh_virtualRouter.csv

aws appmesh list-routes --mesh-name ${MESH_NAME} --virtual-router-name ${router_name}
aws appmesh list-routes --mesh-name ${MESH_NAME} --virtual-router-name ${router_name} | jq -r '.routes[] | ["virtualRouterName", .virtualRouterName ,.routeName] |@csv'

aws appmesh describe-virtual-service --mesh-name ${MESH_NAME} --virtual-service-name ${service_name}
```
 
## ルーターとルート名
```sh
routers=$(aws appmesh list-virtual-routers --mesh-name ${MESH_NAME} | jq -r '.virtualRouters[].virtualRouterName')
for router in $(echo ${routers});
do
aws appmesh list-routes --mesh-name ${MESH_NAME} --virtual-router-name ${router} | jq -r '.routes[] | ["virtualRouterName", .virtualRouterName ,.routeName] |@csv' >> ~/Downloads/mesh_routes.csv
done
```

## ルート&ノード
```sh
for router in $(echo ${routers});
do
route_name=$(aws appmesh list-routes --mesh-name ${MESH_NAME} --virtual-router-name ${router} | jq -r '.routes[].routeName')
aws appmesh describe-route --mesh-name ${MESH_NAME} --virtual-router-name ${router} --route-name ${route_name} | jq -r '["virtualRouterName", .route.virtualRouterName, "routeName", .route.routeName, "virtualNode", .route.spec.httpRoute.action.weightedTargets[].virtualNode] |@csv' >> ~/Downloads/describe_route.csv
done
```

## サービス&ルーター
```sh
services=$(aws appmesh list-virtual-services --mesh-name ${MESH_NAME} | jq -r '.virtualServices[].virtualServiceName')
for service in $(echo ${services});
do
aws appmesh describe-virtual-service --mesh-name ${MESH_NAME} --virtual-service-name ${service} | jq -r '["virtualService", .virtualService.virtualServiceName, "virtualRouterName", .virtualService.spec.provider.virtualRouter.virtualRouterName] |@csv' >> ~/Downloads/describe_service.csv
done
```

## ノード＆バックエンド
```sh
v_nodes=$(aws appmesh list-virtual-nodes --mesh-name ${MESH_NAME} | jq -r '.virtualNodes[].virtualNodeName')
for v_node in $(echo ${v_nodes});
do
aws appmesh describe-virtual-node --mesh-name ${MESH_NAME} --virtual-node-name ${v_node} | jq -r '.virtualNode | ["virtualNode", .virtualNodeName, "backends", .spec.backends[].virtualService.virtualServiceName] | @csv' >> ~/Downloads/describe_node.csv
done
```


# Ne04j初期設定
https://neo4j.com/deployment-center/#gds-tab
"Graph Data Science Self-Managed"をダウンロードして、任意の場所に解凍。
```sh
# ローカル環境のため、まとめてフルアクセスを許可する
chmod -R 777 ~/neo4j
$ ll ~/neo4j
total 360
-rwxrwxrwx@   1 user  staff   36008 Mar 20 19:15 LICENSE.txt
-rwxrwxrwx@   1 user  staff  119015 Mar 20 19:15 LICENSES.txt
-rwxrwxrwx@   1 user  staff   11785 Mar 20 19:15 NOTICE.txt
-rwxrwxrwx@   1 user  staff    1438 Mar 20 19:15 README.txt
-rwxrwxrwx@   1 user  staff      94 Mar 20 19:15 UPGRADE.txt
drwxrwxrwx@   6 user  staff     192 Mar 20 19:20 bin
drwxrwxrwx@   2 user  staff      64 Mar 20 19:15 certificates
drwxrwxrwx@   6 user  staff     192 Mar 21 16:54 conf
drwxrwxrwx@   7 user  staff     224 Apr 13 01:54 data
drwxrwxrwx@   5 user  staff     160 Apr 13 22:47 import
drwxrwxrwx@   5 user  staff     160 Mar 21 16:54 labs
drwxrwxrwx@ 255 user  staff    8160 Mar 21 16:54 lib
drwxrwxrwx@   2 user  staff      64 Mar 20 19:15 licenses
drwxrwxrwx@   7 user  staff     224 Apr 13 01:54 logs
-rwxrwxrwx@   1 user  staff      55 Mar 20 19:15 packaging_info
drwxrwxrwx@   3 user  staff      96 Mar 21 16:54 plugins
drwxrwxrwx@   3 user  staff      96 Mar 21 16:54 products
drwxrwxrwx@   2 user  staff      64 Mar 20 19:15 run

$ ls ~/neo4j/import
appmesh_data.csv        appmesh_data_v3.csv

$ env | grep NEO4J 
NEO4J_HOME=~/neo4j
NEO4J_JAVA=/usr/local/Cellar/openjdk@21/21.0.6/bin/java

$ which neo4j_docker
neo4j_docker: aliased to docker run --publish=7474:7474 --publish=7687:7687 --volume=$NEO4J_HOME/data:/data --volume=$NEO4J_HOME/logs:/logs --volume=$NEO4J_HOME/import:/import neo4j:2025.03.0-community-bullseye
```


## ノード一括作成
```sql
LOAD CSV WITH HEADERS FROM 'file:///appmesh_data.csv' AS row
CREATE (n)
SET n = row,
  n:`${row.label}`
```
## プロパティ調整: backends追加
```sql
LOAD CSV WITH HEADERS FROM 'file:///appmesh_node_backends.csv' AS row
MATCH (n {id: row.id})
WHERE row.relation_name IS NOT NULL
SET n.backends = split(row.relation_name,',')
```

## リレーション
```sql
-- VirtualService と VirtualRouter 
MATCH (service {type: 'VirtualService'})
WHERE service.relation_type = 'VirtualRouter' AND service.relation_name IS NOT NULL
MATCH (router {type: 'VirtualRouter', name: service.relation_name})
MERGE (service)-[r:HAVE]->(router);

-- VirtualRouter と VirtualNode の関係
MATCH (router {type: 'VirtualRouter'})
WHERE router.relation_type = 'VirtualNode' AND router.relation_name IS NOT NULL
MATCH (node {type: 'VirtualNode', name: router.relation_name})
MERGE (router)-[r:ROUTE_TO]->(node);

-- VirtualNode と VirtualService 
MATCH (node {type: 'VirtualNode'})
WHERE node.relation_type = 'VirtualService' AND node.relation_name IS NOT NULL
MATCH (service {type: 'VirtualService', name: node.relation_name})
MERGE (node)-[r:RESOLVED_TO]->(service);

-- VirtualNode と Backends
MATCH (node {type: 'VirtualNode'})
WHERE node.backends IS NOT NULL

WITH node, node.backends AS backends
UNWIND backends AS backend

MATCH (service {name: backend})
MERGE (node)-[r:REQUEST_TO]->(service);


-- Namespace と Cluster
MATCH (namespace {type: 'Namespace'})
WHERE namespace.cluster IS NOT NULL
MATCH (cluster {type: 'Cluster', name: namespace.cluster})
MERGE (namespace)-[r:BELONG_TO]->(cluster);
```


match (n)-[r]-(nn)
return n,r,nn
