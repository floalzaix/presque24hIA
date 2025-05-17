from server.game_api import GameApi

class Bot:
    def __init__(self, api: GameApi):
        self.api = api
        self.defense_cards = {'number': 0, 'value': 0}
        self.attaque_cards = {'number': 0, 'value': 0}
        self.savoir_cards = {'number': 0, 'value': 0}

    def get_current_hp(self) -> int:
        return int(self.api.moi()[0])

    def get_current_defense(self) -> int:
        return int(self.api.moi()[1])

    def get_current_attack(self) -> int:
        return int(self.api.moi()[2])

    def get_current_turn(self) -> int:
        return int(self.api.numero_tour)

    def get_phase(self) -> int:
        return int(self.api.numero_phase)

    def get_monsters(self) -> list[dict]:
        """
        Returns a list of dicts:
        [{'id': 0, 'PV': 100, 'gain': 400}, ...]
        """
        raw = self.api.monstres()
        infos = []
        for i in range(len(raw)):
            pv = int(raw[i][0])
            pv_max = ((self.get_current_turn() - 1) // 3) * 30 + 10
            infos.append({'id': i, 'PV': pv, 'gain': int(raw[i][1]), 'touche_par_personne': pv == pv_max})
        
        return infos

    def get_expeditions(self) -> list[dict]:
        """
        Returns:
        [{'id': 0, 'type': 'DEFENSE', 'val': 3}, ...]
        """
        raw = self.api.pioches()
        return [
            {'id': i, 'type': raw[i][0], 'val': int(raw[i][1])}
            for i in range(len(raw))
        ]

    def send_piocher(self, slot: int):
        val = self.get_expeditions()[slot]['val']
        if val > 0:
            if slot in [0,3]:
                self.defense_cards['number'] += 1
                self.defense_cards['value'] += val

            elif slot in [1,4]:
                self.attaque_cards['number'] += 1
                self.attaque_cards['value'] += val

            elif slot in [2,5]:
                self.savoir_cards['number'] += 1
                self.savoir_cards['value'] += val
        self.api.piocher(slot)

    def send_utiliser(self, type_carte: str):
        self.api.utiliser(type_carte)

    def send_attaquer(self, monster_id: int):
        self.api.attaquer(monster_id)

    def end_turn(self):
        self.api.end_tour()

    def get_team_num(self) -> int:
        return self.api.team_num

    def get_dame_rouge_degats(self) -> int:
        return int(self.api.degats())