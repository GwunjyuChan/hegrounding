"""San Sebastian, July-August 1813: text-first items from Jones, Journals of Sieges, 3rd ed. (1846), vol. II, ch. II,
on maps/napoleon_maps/san_sebastian_1813.jpg. Replaces the AI paraphrases of MF0013-0016 (whose originals were modern,
copyrighted web texts) with verbatim public-domain passages. MF0014-0016 keep their IDs and geometry; MF0013 keeps its
ID, its geometry is redrawn to the convent post Jones names. Jones's pages interleave footnotes quoting Belmas in French;
the passages below are cut between them, so no footnote text enters the model input."""
import sys; sys.path.insert(0, "benchmark/sources")
from textfirst_lib import RAW, write, map_record

IMAGE = "maps/napoleon_maps/san_sebastian_1813.jpg"
M = map_record(IMAGE)
JONES_HEAD = [r"^IN SPAIN AND PORTUGAL\.", r"^JOURNALS OF SIEGES$", r"^\d{1,3}$", r"^TIAN\. '?$", r"^Second Sie-e,"]
SPEC = dict(
    battle_id="san_sebastian_1813", created="2026-10-21", image=IMAGE, img_w=M["img_w"], img_h=M["img_h"],
    map_url=M["map_url"], map_provenance=M["map_provenance"],
    sources=dict(jones=dict(
        file=RAW + "bergen_jones1846_v2_journalsofsieges02jone_djvu.txt", archive_id="journalsofsieges02jone",
        citation="Sir John T. Jones, Journals of Sieges carried on by the Army under the Duke of Wellington, in Spain, "
                 "during the years 1811 to 1814, 3rd ed., ed. Harry D. Jones, vol. II (London: John Weale, 1846), "
                 "ch. II 'Siege of St. Sebastian, between 11th July and 8th September 1813'",
        source_kind="secondary_history by a Royal Engineers officer (engineer's journal)",
        rights_basis="published 1846; author d. 1843, editor d. 1866")),
    passages=dict(
        plan=dict(source="jones", pages="p. 17", drop=JONES_HEAD,
            start="On the proposition of Major Charles F. Smith", end="whilst marching to the assault.",
            fixes=[]),
        convent=dict(source="jones", pages="p. 26", drop=JONES_HEAD,
            start="At 10 o'clock A.M. the convent and redoubt were", end="wounded prisoners.",
            fixes=[("unnecessaril}^", "unnecessarily")]),
        batteries=dict(source="jones", pages="p. 27", drop=JONES_HEAD,
            start="As soon as the convent was carried, a working", end="No. 4, for two 8-inch howitzers.",
            fixes=[]),
        island=dict(source="jones", pages="pp. 61-62", drop=JONES_HEAD,
            start="It being reported that notwithstanding the ex", end="for those purposes.",
            fixes=[("off\" the entrance", "off the entrance"), ("St. Sebas- reverse", "reverse"), ("ui3on", "upon")]),
        town=dict(source="jones", pages="p. 79", drop=JONES_HEAD,
            start="The principal square and every street presented", end="convent of St. Teresa.",
            fixes=[]),
    ),
    items=[
     dict(event_id="MF0013", replaces="MF0013", passage="plan",
          question="Which post in advance of the town were the operations on the isthmus confined to dislodging the garrison from? Mark the location.",
          question_zh="地峡上的行动只限于把守军从城前哪个据点赶走？", answer_zh="St. Bartolomeo 修道院和旁边的小多面堡（城前约 700-800 码）",
          text_evidence="formed by the convent of St. Bartolomeo and a small redoubt",
          map_evidence="Convent on the Heights of St. Bartholomew south of the Suburb of St. Martin, with the small works beside it.",
          geometry={"type": "polygon", "coordinates": [[525, 535], [585, 535], [590, 560], [570, 580], [530, 575]]},
          geometry_source="assistant_redraw (old MF0013 marked the Suburb of St. Martin from a modern paraphrase)",
          tag="place_lookup", confidence_draft=3, time="1813-07, plan of the first siege"),
     dict(event_id="MF0014", replaces="MF0014", passage="plan",
          question="From where were the two breaches in the town wall to be formed? Mark the area.",
          question_zh="城墙上的两个缺口计划从哪里的炮台轰开？", answer_zh="Urumea 河对岸的 Chofre 沙丘（远距离炮台）",
          text_evidence="decided to form two breaches in the town wall from distant batteries on the Chofre sand-hills",
          map_evidence="Chofre Sandhills east of the Urumea, with the numbered breaching batteries.",
          geometry={"type": "polygon", "coordinates": [[846, 371], [877, 337], [941, 314], [989, 300], [1018, 347], [1045, 398], [987, 415], [916, 430], [849, 420]]},
          geometry_source="kept_from_MF0014", tag="place_lookup", confidence_draft=3, time="1813-07, plan of the first siege"),
     dict(event_id="MF0015", replaces="MF0015", passage="island",
          question="On which island was it decided to construct a battery, because it enfilades and sees in reverse the defences of the castle? Mark the location.",
          question_zh="因为能纵射并从背后看到城堡防御，决定在哪个岛上建炮台？", answer_zh="Santa Clara 岛",
          text_evidence="As the island of Santa Clara enfilades and sees in reverse the defences of the castle, it was decided to construct a battery upon it",
          map_evidence="Isle of Santa Clara in the bay west of Monte Orgullo, with battery 10.",
          geometry={"type": "polygon", "coordinates": [[274, 170], [292, 148], [337, 144], [369, 152], [383, 173], [370, 188], [335, 196], [292, 190]]},
          geometry_source="kept_from_MF0015", tag="place_lookup", confidence_draft=4, time="1813-08-26/27, night"),
     dict(event_id="MF0016", replaces="MF0016", passage="town",
          question="Where did the remainder of the garrison take refuge when the town was stormed? Mark the location.",
          question_zh="城被攻破后，剩下的守军退到了哪里？", answer_zh="城堡（Monte Orgullo 上）和 St. Teresa 修道院",
          text_evidence="the remainder took refuge in the castle and the convent of St. Teresa",
          map_evidence="Castle of La Mota on Monte Orgullo north of the town; the convent of St. Teresa is not labelled and lies at the foot of the hill.",
          geometry={"type": "polygon", "coordinates": [[507, 143], [541, 119], [608, 106], [653, 123], [677, 151], [694, 190], [684, 212], [635, 226], [553, 215], [511, 192]]},
          geometry_source="kept_from_MF0016", tag="place_lookup", confidence_draft=3, time="1813-08-31, the assault"),
     dict(event_id="MF0138", passage="convent",
          question="After carrying the convent and redoubt, where did the assailants push down to, exposing themselves to a severe fire from the place? Mark the area.",
          question_zh="攻下修道院和多面堡后，进攻部队冲下山到了哪里，结果暴露在要塞火力下？", answer_zh="山下的地峡（迎击从城里出来的守军）",
          text_evidence="pushed down the hill to the isthmus, to meet a body of the garrison approaching from the town",
          map_evidence="Low ground of the isthmus between the convent heights and the hornwork of the land front, around the Suburb of St. Martin.",
          geometry={"type": "polygon", "coordinates": [[510, 470], [600, 460], [640, 420], [690, 390], [715, 430], [660, 490], [610, 530], [540, 530], [505, 505]]},
          tag="place_lookup", confidence_draft=2, time="1813-07-17, 10 a.m."),
     dict(event_id="MF0139", passage="batteries",
          question="Where were two batteries commenced at dusk, with a great command over the land front? Mark the area.",
          question_zh="黄昏时在哪里开始修两座能居高控制陆正面的炮台？", answer_zh="地峡上的 St. Bartolomeo 高地",
          text_evidence="At dusk two batteries were commenced on the heights of St. Bartolomeo on the isthmus",
          map_evidence="Heights of St. Bartholomew south-west of the convent, where batteries 3 and 4 are drawn.",
          geometry={"type": "polygon", "coordinates": [[420, 530], [560, 525], [590, 560], [560, 600], [480, 650], [430, 620], [410, 570]]},
          tag="place_lookup", confidence_draft=2, time="1813-07-17, dusk"),
    ])

if __name__ == "__main__":
    write(SPEC, "benchmark/sources/text_first/san_sebastian_1813_2026-10-21.jsonl")
