# 苏黎世战役：10 条问题与完整文本

> 核对版，整理于 2026-09-23。对应 Z0001–Z0010 历史事件，不是新地名诊断集 P001–P008。

## 文件说明

- 数据来源：[zurich_pilot_10.jsonl](benchmark/zurich_pilot_10.jsonl)。
- 已逐条核对，以下英文问题和英文文本与既有十条评测的冻结输入完全一致：[input.zip](benchmark/atlas/runs/zurich10_20260916_162847/input.zip)。
- **“英文问题”和“英文文本”是模型输入中的问题与 passage，保留原文，不作摘要或改写。** 地图和系统提示词不在本文件内。
- **“中文辅助理解”是本文件新加的阅读辅助，不是模型实际收到的文字。**
- 英文文本是依据法文史料整理的助手译文，数据中的翻译审核状态仍为 pending；法文原段落附在文末，便于核查。
- 十道题共享四个史料段落。同一段落全文会在相关题目下重复，这是实际输入，不是十段独立史料。
- 本文件不包含标准答案或模型预测，也不修改已有人工标注。

## 史料来源

- 作者：Adolphe Thiers；出版年：1839。
- 书名：Histoire de la Revolution Francaise, tome dixieme, neuvieme edition。
- [在线法文全文](https://www.gutenberg.org/files/13607/13607-h/13607-h.htm)；[本地缓存](benchmark/sources/zurich_thiers_1839.html)。
- 这是战役之后出版的回顾性二手叙述，不是 1799 年的现场记录。
- 下文 p347 等编号是数据中 source_paragraph_index 的提取段落编号，不是书籍页码。

## 目录

- [Z0001](#z0001)：最初乘船渡河后，在 Gazan 集结更多增援之前，首批六百名法国士兵在哪里登陆？
- [Z0002](#z0002)：Gazan 获得增援后进攻时，那三个俄军营正在哪里防守？
- [Z0003](#z0003)：桥梁架设完毕且主力完成渡河后，Bontemps 旅被部署在哪里以应对 Durasof，而不是跟随 Oudinot 向上游推进？
- [Z0004](#z0004)：在 Massena 命令 Klein 师开始行动之前，该师驻扎在哪里？这里问的不是 Humbert 随后行进的地点。
- [Z0005](#z0005)：Oudinot 在向上游推进过程中夺取了哪片高地？请区别于同段落提到的小型营地和主要道路。
- [Z0006](#z0006)：在首批六百人登船之前，法军为在 Dietikon 附近渡河，排列在河岸的什么位置？
- [Z0007](#z0007)：在最初向苏黎世推进时，也就是被迫后退之前、Humbert 介入之前，Mortier 经由哪个地方接近城市？请在地图上标出这个地方。
- [Z0008](#z0008)：Oudinot 的部队沿利马特河向上游推进时，攻占的小型营地在哪里？请区别于苏黎世后方的高地和段落中提到的道路。
- [Z0009](#z0009)：Oudinot 向上游推进时，夺取了哪条供俄军向德国撤退的道路？请标出苏黎世附近能够辨认的路段，而不是道路远端的城镇。
- [Z0010](#z0010)：Korsakoff 意识到自己的处境并调动部队之后、下文描述的次日早晨战斗之前，他的部队当时部署在苏黎世相对于利马特河的哪个部分？

<a id="z0001"></a>

## Z0001

史料定位：[第 347 段法文原文](#source-p347)。

### 英文问题（模型输入）

Immediately after their initial boat crossing, where did the first six hundred French soldiers land, before Gazan assembled further reinforcements?

### 中文辅助理解（非模型输入）

最初乘船渡河后，在 Gazan 集结更多增援之前，首批六百名法国士兵在哪里登陆？

### 英文文本（模型输入，完整段落）

These arrangements, which had won the admiration of all the critics, were put into execution on 3 Vendemiaire, Year VIII (25 September 1799), at five in the morning. Preparations for the crossing had been made near the village of Dietikon with extraordinary care and secrecy. Boats had been dragged by hand and hidden in the woods. By morning they were afloat, and the troops were silently drawn up on the bank. General Foy, later distinguished as an orator, commanded the artillery in this memorable battle; he positioned several batteries to protect the crossing. Six hundred men boldly embarked and reached the opposite bank. They immediately attacked and scattered the enemy skirmishers. Korsakoff had stationed three battalions with artillery there, on the plateau of Closter-Fahr. Our artillery, skilfully directed, soon silenced the Russian guns and protected the successive crossings of our advance guard. When General Gazan had assembled sufficient reinforcements with the six hundred men who had crossed first, he advanced against the three Russian battalions guarding Closter-Fahr. They had established themselves in a wood and defended it bravely. Gazan surrounded them and had to kill almost every last man to dislodge them. Once these three battalions had been destroyed, the bridge was laid. The rest of Lorge's division and part of Mesnard's division crossed the Limmat: fifteen thousand men had been brought across the river. Bontemps's brigade was stationed at Regensdorf to face Durasof should he move up from the lower Limmat. The main body, directed by chief of staff Oudinot, moved upstream along the Limmat to reach the rear of Zurich.

<a id="z0002"></a>

## Z0002

史料定位：[第 347 段法文原文](#source-p347)。

### 英文问题（模型输入）

Where were the three Russian battalions defending when Gazan attacked them after receiving reinforcements?

### 中文辅助理解（非模型输入）

Gazan 获得增援后进攻时，那三个俄军营正在哪里防守？

### 英文文本（模型输入，完整段落）

These arrangements, which had won the admiration of all the critics, were put into execution on 3 Vendemiaire, Year VIII (25 September 1799), at five in the morning. Preparations for the crossing had been made near the village of Dietikon with extraordinary care and secrecy. Boats had been dragged by hand and hidden in the woods. By morning they were afloat, and the troops were silently drawn up on the bank. General Foy, later distinguished as an orator, commanded the artillery in this memorable battle; he positioned several batteries to protect the crossing. Six hundred men boldly embarked and reached the opposite bank. They immediately attacked and scattered the enemy skirmishers. Korsakoff had stationed three battalions with artillery there, on the plateau of Closter-Fahr. Our artillery, skilfully directed, soon silenced the Russian guns and protected the successive crossings of our advance guard. When General Gazan had assembled sufficient reinforcements with the six hundred men who had crossed first, he advanced against the three Russian battalions guarding Closter-Fahr. They had established themselves in a wood and defended it bravely. Gazan surrounded them and had to kill almost every last man to dislodge them. Once these three battalions had been destroyed, the bridge was laid. The rest of Lorge's division and part of Mesnard's division crossed the Limmat: fifteen thousand men had been brought across the river. Bontemps's brigade was stationed at Regensdorf to face Durasof should he move up from the lower Limmat. The main body, directed by chief of staff Oudinot, moved upstream along the Limmat to reach the rear of Zurich.

<a id="z0003"></a>

## Z0003

史料定位：[第 347 段法文原文](#source-p347)。

### 英文问题（模型输入）

After the bridge was laid and the main crossing completed, where was Bontemps's brigade stationed to face Durasof, rather than following Oudinot upstream?

### 中文辅助理解（非模型输入）

桥梁架设完毕且主力完成渡河后，Bontemps 旅被部署在哪里以应对 Durasof，而不是跟随 Oudinot 向上游推进？

### 英文文本（模型输入，完整段落）

These arrangements, which had won the admiration of all the critics, were put into execution on 3 Vendemiaire, Year VIII (25 September 1799), at five in the morning. Preparations for the crossing had been made near the village of Dietikon with extraordinary care and secrecy. Boats had been dragged by hand and hidden in the woods. By morning they were afloat, and the troops were silently drawn up on the bank. General Foy, later distinguished as an orator, commanded the artillery in this memorable battle; he positioned several batteries to protect the crossing. Six hundred men boldly embarked and reached the opposite bank. They immediately attacked and scattered the enemy skirmishers. Korsakoff had stationed three battalions with artillery there, on the plateau of Closter-Fahr. Our artillery, skilfully directed, soon silenced the Russian guns and protected the successive crossings of our advance guard. When General Gazan had assembled sufficient reinforcements with the six hundred men who had crossed first, he advanced against the three Russian battalions guarding Closter-Fahr. They had established themselves in a wood and defended it bravely. Gazan surrounded them and had to kill almost every last man to dislodge them. Once these three battalions had been destroyed, the bridge was laid. The rest of Lorge's division and part of Mesnard's division crossed the Limmat: fifteen thousand men had been brought across the river. Bontemps's brigade was stationed at Regensdorf to face Durasof should he move up from the lower Limmat. The main body, directed by chief of staff Oudinot, moved upstream along the Limmat to reach the rear of Zurich.

<a id="z0004"></a>

## Z0004

史料定位：[第 348 段法文原文](#source-p348)。

### 英文问题（模型输入）

Where was Klein's division stationed immediately before Massena set it in motion, rather than where Humbert subsequently marched?

### 中文辅助理解（非模型输入）

在 Massena 命令 Klein 师开始行动之前，该师驻扎在哪里？这里问的不是 Humbert 随后行进的地点。

### 英文文本（模型输入，完整段落）

Once this part of the operation was completed, Massena personally returned to the other bank of the Limmat to oversee the movements of his wings. On the lower Limmat, Mesnard had so thoroughly deceived Durasof with his demonstrations that the latter had moved to the bank and opened fire with all his guns. On his right, Mortier had advanced towards Zurich by way of Wollishofen, but had encountered Korsakoff's main force, positioned, as already stated, in front of the Limmat, and had been compelled to fall back. Arriving at that moment, Massena set Klein's division, which was at Altstetten, in motion. Humbert, at the head of his four thousand grenadiers, marched on Zurich and restored the battle. Mortier renewed his attacks, and the Russians were thus confined within Zurich.

<a id="z0005"></a>

## Z0005

史料定位：[第 349 段法文原文](#source-p349)。

### 英文问题（模型输入）

Which high-ground area had Oudinot captured during his upstream advance, distinct from the small camp and the main road also mentioned?

### 中文辅助理解（非模型输入）

Oudinot 在向上游推进过程中夺取了哪片高地？请区别于同段落提到的小型营地和主要道路。

### 英文文本（模型输入，完整段落）

Meanwhile, Korsakoff, troubled by hearing cannon fire in his rear, had sent some battalions back across the Limmat, but these weak reinforcements had been of no use. Oudinot, with his fifteen thousand men, continued moving upstream along the Limmat. He had captured the small camp at Hong, as well as the heights behind Zurich, and had seized the main road to Vintherthur, which led into Germany and was the only route by which the Russians could retreat.

<a id="z0006"></a>

## Z0006

史料定位：[第 347 段法文原文](#source-p347)。

### 英文问题（模型输入）

Before the first six hundred men embarked, where were the French troops drawn up on the river bank for the crossing near Dietikon?

### 中文辅助理解（非模型输入）

在首批六百人登船之前，法军为在 Dietikon 附近渡河，排列在河岸的什么位置？

### 英文文本（模型输入，完整段落）

These arrangements, which had won the admiration of all the critics, were put into execution on 3 Vendemiaire, Year VIII (25 September 1799), at five in the morning. Preparations for the crossing had been made near the village of Dietikon with extraordinary care and secrecy. Boats had been dragged by hand and hidden in the woods. By morning they were afloat, and the troops were silently drawn up on the bank. General Foy, later distinguished as an orator, commanded the artillery in this memorable battle; he positioned several batteries to protect the crossing. Six hundred men boldly embarked and reached the opposite bank. They immediately attacked and scattered the enemy skirmishers. Korsakoff had stationed three battalions with artillery there, on the plateau of Closter-Fahr. Our artillery, skilfully directed, soon silenced the Russian guns and protected the successive crossings of our advance guard. When General Gazan had assembled sufficient reinforcements with the six hundred men who had crossed first, he advanced against the three Russian battalions guarding Closter-Fahr. They had established themselves in a wood and defended it bravely. Gazan surrounded them and had to kill almost every last man to dislodge them. Once these three battalions had been destroyed, the bridge was laid. The rest of Lorge's division and part of Mesnard's division crossed the Limmat: fifteen thousand men had been brought across the river. Bontemps's brigade was stationed at Regensdorf to face Durasof should he move up from the lower Limmat. The main body, directed by chief of staff Oudinot, moved upstream along the Limmat to reach the rear of Zurich.

<a id="z0007"></a>

## Z0007

史料定位：[第 348 段法文原文](#source-p348)。

### 英文问题（模型输入）

During his initial advance towards Zurich, before being forced to fall back and before Humbert intervened, through which locality did Mortier approach the city? Mark that locality on the map.

### 中文辅助理解（非模型输入）

在最初向苏黎世推进时，也就是被迫后退之前、Humbert 介入之前，Mortier 经由哪个地方接近城市？请在地图上标出这个地方。

### 英文文本（模型输入，完整段落）

Once this part of the operation was completed, Massena personally returned to the other bank of the Limmat to oversee the movements of his wings. On the lower Limmat, Mesnard had so thoroughly deceived Durasof with his demonstrations that the latter had moved to the bank and opened fire with all his guns. On his right, Mortier had advanced towards Zurich by way of Wollishofen, but had encountered Korsakoff's main force, positioned, as already stated, in front of the Limmat, and had been compelled to fall back. Arriving at that moment, Massena set Klein's division, which was at Altstetten, in motion. Humbert, at the head of his four thousand grenadiers, marched on Zurich and restored the battle. Mortier renewed his attacks, and the Russians were thus confined within Zurich.

<a id="z0008"></a>

## Z0008

史料定位：[第 349 段法文原文](#source-p349)。

### 英文问题（模型输入）

While Oudinot's force was moving upstream along the Limmat, where was the small camp that it captured, as distinct from the heights behind Zurich and the road also mentioned in the paragraph?

### 中文辅助理解（非模型输入）

Oudinot 的部队沿利马特河向上游推进时，攻占的小型营地在哪里？请区别于苏黎世后方的高地和段落中提到的道路。

### 英文文本（模型输入，完整段落）

Meanwhile, Korsakoff, troubled by hearing cannon fire in his rear, had sent some battalions back across the Limmat, but these weak reinforcements had been of no use. Oudinot, with his fifteen thousand men, continued moving upstream along the Limmat. He had captured the small camp at Hong, as well as the heights behind Zurich, and had seized the main road to Vintherthur, which led into Germany and was the only route by which the Russians could retreat.

<a id="z0009"></a>

## Z0009

史料定位：[第 349 段法文原文](#source-p349)。

### 英文问题（模型输入）

During Oudinot's upstream advance, which road did his force seize that provided the Russians' route of retreat towards Germany? Mark the identifiable part of that road near Zurich, not the town at its far end.

### 中文辅助理解（非模型输入）

Oudinot 向上游推进时，夺取了哪条供俄军向德国撤退的道路？请标出苏黎世附近能够辨认的路段，而不是道路远端的城镇。

### 英文文本（模型输入，完整段落）

Meanwhile, Korsakoff, troubled by hearing cannon fire in his rear, had sent some battalions back across the Limmat, but these weak reinforcements had been of no use. Oudinot, with his fifteen thousand men, continued moving upstream along the Limmat. He had captured the small camp at Hong, as well as the heights behind Zurich, and had seized the main road to Vintherthur, which led into Germany and was the only route by which the Russians could retreat.

<a id="z0010"></a>

## Z0010

史料定位：[第 351 段法文原文](#source-p351)。

### 英文问题（模型输入）

After Korsakoff recognized his predicament and moved his troops, but before the fighting described for the next morning, in which part of Zurich relative to the Limmat were his troops now positioned?

### 中文辅助理解（非模型输入）

Korsakoff 意识到自己的处境并调动部队之后、下文描述的次日早晨战斗之前，他的部队当时部署在苏黎世相对于利马特河的哪个部分？

### 英文文本（模型输入，完整段落）

Korsakoff had finally realized his situation and had moved his troops into the other part of Zurich, behind the Limmat. Durasof, on the lower Limmat, had slipped away on learning of the crossing; avoiding Bontemps's brigade by a detour, he had regained the road to Vintherthur. The next day, 4 Vendemiaire (26 September), the fighting was to be fierce, for the Russians wanted to force a way out and the French wanted to take great spoils. Fighting began early. The unfortunate city of Zurich, crowded with artillery, baggage and wounded men and attacked from every side, seemed enveloped in fire. On this side of the Limmat, Mortier and Klein had reached the city and were about to enter it. Beyond the river, Oudinot pressed it from the rear and sought to block Korsakoff's route. This road to Vintherthur, the scene of bloody fighting, had been taken and retaken several times. Finally deciding to withdraw, Korsakoff placed his infantry at the head, his cavalry in the centre, and his artillery and baggage at the rear. He advanced in this way in a long column. His brave infantry, charging furiously, swept everything before it and opened a passage; but after it had passed with part of the cavalry, the French charged again, attacked the remaining cavalry and baggage, and drove them back to the gates of Zurich. At the same moment, Klein and Mortier entered from their side. Fighting took place in the streets. The renowned and unfortunate Lavater was struck at the door of his house by a bullet fired by a drunken Swiss soldier who had put his musket to his chest to demand money; he fell with a serious wound to his thigh, from which he died some months later. Finally, all those who had remained in Zurich were forced to lay down their arms. One hundred cannon, all the baggage, the administrative services, the army treasury and five thousand prisoners fell into French hands. Korsakoff had also had eight thousand men put out of action in this bitter struggle. Eight and five made thirteen thousand men lost, that is, half his army. The great battles in Italy had produced no more extraordinary results. The consequences for the rest of the campaign were to be no less important than the material gains. Korsakoff, with at most thirteen thousand men, hastened back to the Rhine.

## 附录：法文原段落

以下 source_text 按提取段落编号去重保存；对应关系列于各段标题下。

<a id="source-p347"></a>

### 第 347 段

对应问题：Z0001、Z0002、Z0003、Z0006。

Ces dispositions, qui ont fait l'admiration de tous les critiques, furent mises à exécution le 3 vendémiaire an VIII (25 septembre 1799), à cinq heures du matin. Les apprêts du passage avaient été faits près du village de Dietikon, avec un soin et un secret extraordinaires. Des barques avaient été traînées à bras, et cachées dans les bois. Dès le matin, elles étaient à flot, et les troupes étaient rangées en silence sur la rive. Le général Foy, illustré depuis comme orateur, commandait l'artillerie à cette immortelle bataille; il disposa plusieurs batteries de manière à protéger le passage. Six cents hommes s'embarquèrent hardiment, et arrivèrent sur l'autre rive. Sur-le-champ ils fondirent sur les tirailleurs ennemis, et les dispersèrent. Korsakoff avait mis là, sur le plateau de Closter-Fahr, trois bataillons avec du canon. Notre artillerie, supérieurement dirigée, éteignit bientôt les feux de l'artillerie russe, et protégea le passage successif de notre avant-garde. Lorsque le général Gazan eut réuni aux six cents hommes qui avaient passé les premiers un renfort suffisant, il marcha sur les trois bataillons russes qui gardaient Closter-Fahr. Ceux-ci s'étaient logés dans un bois, et s'y défendirent bravement. Gazan les enveloppa, et fut obligé de tuer presque jusqu'au dernier homme pour les déloger. Ces trois bataillons détruits, le pont fut jeté. Le reste de la division Lorge et partie de la division Mesnard passèrent la Limmat: c'étaient quinze mille hommes portés au-delà de la rivière. La brigade Bontemps fut placée à Regensdorf, pour faire face à Durasof, s'il voulait remonter de la Basse-Limmat. Le gros des troupes, dirigé par le chef d'état-major Oudinot, remonta la Limmat, pour se porter sur les derrières de Zurich.

<a id="source-p348"></a>

### 第 348 段

对应问题：Z0004、Z0007。

Cette partie de l'opération achevée, Masséna se reporta de sa personne sur l'autre rive de la Limmat, pour veiller au mouvement de ses ailes. Vers la Basse-Limmat, Mesnard avait si bien trompé Durasof par ses démonstrations, que celui-ci s'était porté sur la rive, où il déployait tous ses feux. A sa droite, Mortier s'était avancé sur Zurich par Wollishofen, mais il y avait rencontré la masse de Korsakoff, posté, comme on l'a dit, en avant de la Limmat, et avait été obligé de se replier. Masséna arrivant dans cet instant ébranla la division Klein, qui était à Altstetten. Humbert, à la tête de ses quatre mille grenadiers, marcha sur Zurich, et rétablit le combat. Mortier renouvela ses attaques, et on parvint à renfermer ainsi les Russes dans Zurich.

<a id="source-p349"></a>

### 第 349 段

对应问题：Z0005、Z0008、Z0009。

Pendant ce temps, Korsakoff, chagriné d'entendre du canon sur ses derrières, avait reporté quelques bataillons au-delà de la Limmat; mais ces faibles secours avaient été inutiles. Oudinot, avec ses quinze mille hommes, continuait à remonter la Limmat. Il avait enlevé le petit camp placé à Hong, ainsi que les hauteurs qui sont sur les derrières de Zurich, et s'était emparé de la grande route de Vintherthur, qui donne issue en Allemagne, et la seule par laquelle les Russes pussent se retirer.

<a id="source-p351"></a>

### 第 351 段

对应问题：Z0010。

Korsakoff s'était enfin aperçu de sa position, et avait porté ses troupes dans l'autre partie de Zurich, en arrière de la Limmat. Durasof, sur la Basse-Limmat, apprenant le passage, s'était dérobé; et évitant la brigade Bontemps, par un détour, était venu regagner la route de Vintherthur. Le lendemain 4 vendémiaire (26 septembre), le combat devait être acharné, car les Russes voulaient se faire jour, et les Français voulaient recueillir d'immenses trophées. Le combat commença de bonne heure. La malheureuse ville de Zurich, encombrée d'artillerie, d'équipages, de blessés, attaquée de tous côtés, était comme enveloppée de feux. De ce côté-ci de la Limmat, Mortier et Klein l'avaient abordée, et étaient près d'y pénétrer. Au-delà, Oudinot la serrait par derrière et voulait fermer la route à Korsakoff. Cette route de Vintherthur, théâtre d'un combat sanglant, avait été prise et reprise plusieurs fois. Korsakoff, songeant enfin à se retirer, avait mis son infanterie en tête, sa cavalerie au centre, son artillerie et ses équipages à la queue. Il s'avançait ainsi formant une longue colonne. Sa brave infanterie, chargeant avec furie, renverse tout devant elle, et s'ouvre un passage; mais quand elle a passé avec une partie de la cavalerie, les Français reviennent à la charge, attaquent le reste de la cavalerie et les bagages, et les refoulent jusqu'aux portes de Zurich. Au même instant, Klein, Mortier, y entrent de leur côté. On se bat dans les rues. L'illustre et malheureux Lavater est frappé sur la porte de sa maison, d'une balle par un soldat suisse ivre qui lui mit son fusil sur la poitrine pour avoir de l'argent; il tomba atteint d'une blessure grave à la cuisse dont il mourut quelques mois après. Enfin, tout ce qui était resté dans Zurich est obligé de mettre bas les armes. Cent pièces de canon, tous les bagages, les administrations, le trésor de l'armée et cinq mille prisonniers, deviennent la proie des Français. Korsakoff avait eu en outre huit mille hommes hors de combat, dans cette lutte acharnée. Huit et cinq faisaient treize mille hommes perdus, c'est-à-dire la moitié de son armée. Les grandes batailles d'Italie n'avaient pas présenté des résultats plus extraordinaires. Les conséquences pour le reste de la campagne ne devaient pas être moins grandes que les résultats matériels. Korsakoff, avec treize mille hommes au plus, se hâta de regagner le Rhin.

