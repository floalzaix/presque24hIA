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
        print(self.api.numero_phase)
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
            infos.append({'id': i, 'PV': pv, 'gain': int(raw[i][1]), 'est_blesse': pv != pv_max})
        
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
    
    def get_total_defense(self) -> int:
        hp = self.get_current_hp()
        defense = self.get_current_defense()
        nb_cards = self.defense_cards['number']
        value = self.defense_cards['value']
        defense_card = value if nb_cards <=4 else int(value*1.5) if nb_cards <= 8 else value*2
        return hp + defense + defense_card
    
    def get_best_slot(self, *types) -> int|None:
        pioche = self.get_expeditions()
        meilleurs = [slot for slot in pioche if slot['type'] in types and slot['val'] > 0]
        if not meilleurs:
            return None
        return max(meilleurs, key=lambda s: s['val'])['id']


    def play_turns(self):
        tour_actuel = self.get_current_turn()

        # 1. Calcul des dégâts cumulés jusqu’au tour 15 (avec +15 à chaque lune)
        degats = 10
        total_degats = 0
        for tour in range(1, 16):
            total_degats += degats + 15
            degats += 15 + 2  # 3 monstres + bonus

        # 2. Estimation de la défense nécessaire
        defense_voulue = total_degats
        defense_actuelle = self.get_total_defense()
        defense_a_faire = max(0, defense_voulue - defense_actuelle)
        tours_restants = max(1, 15 - tour_actuel + 1)
        defense_par_tour = defense_a_faire // tours_restants

        # 3. Calcul de l’attaque requise pour 2000 pts de savoir (500 PV à tuer seul)
        nb_tours_exploitables = max(1, int(0.75 * max(0, 15 - max(9, tour_actuel) + 1)))
        attaque_par_tour = 500 // nb_tours_exploitables
        attaque_objectif_cartes = 250  # x2 avec >8 cartes

        # 4. Vérifier si risque de mort (tour 15 + pas assez de défense)
        if tour_actuel == 15 and self.get_total_defense() < total_degats:
            if self.defense_cards['number'] > 0:
                self.send_utiliser("DEFENSE")
            if self.savoir_cards['number'] > 0:
                self.send_utiliser("SAVOIR")
            self.end_turn()
            return

        # 5. Vérifier si attaque est prête ET on est dans une phase de nuit
        if self.attaque_cards['value'] >= attaque_objectif_cartes:
            # Vérifier qu’on est bien dans une phase de nuit
            if (self.get_phase() + 1) % 4 == 0:
                monstres = self.get_monsters()
                monstres_vierges = [m for m in monstres if not m['est_blesse'] and m['PV'] > 0]

                if monstres_vierges:
                    self.send_utiliser("ATTAQUE")
                    self.send_attaquer(monstres_vierges[0]['id'])
                    return
                else:
                    # Aucun monstre vierge disponible
                    slot = self.get_best_slot("DEFENSE", "SAVOIR")
                    if slot is not None:
                        self.send_piocher(slot)
                    else:
                        self.end_turn()
                    return
            else:
                # Pas la bonne phase pour attaquer → fallback vers pioche
                slot = self.get_best_slot("DEFENSE", "SAVOIR")
                if slot is not None:
                    self.send_piocher(slot)
                else:
                    self.end_turn()
                return

        # 6. Sinon, attaque insuffisante → piocher attaque
        if self.attaque_cards['value'] < attaque_objectif_cartes:
            slot = self.get_best_slot("ATTAQUE")
            if slot is not None:
                self.send_piocher(slot)
            else:
                # fallback si aucune attaque dispo
                slot = self.get_best_slot("DEFENSE", "SAVOIR")
                if slot is not None:
                    self.send_piocher(slot)
                else:
                    self.end_turn()
            return

        # 7. Sinon, vérifier si défense encore à compléter
        if self.defense_cards['value'] < defense_par_tour * tours_restants:
            slot = self.get_best_slot("DEFENSE")
            if slot is not None:
                self.send_piocher(slot)
            else:
                slot = self.get_best_slot("ATTAQUE", "SAVOIR")
                if slot is not None:
                    self.send_piocher(slot)
                else:
                    self.end_turn()
            return

        # 8. Sinon, tout va bien → piocher savoir
        slot = self.get_best_slot("SAVOIR")
        if slot is not None:
            self.send_piocher(slot)
        else:
            # fallback
            slot = self.get_best_slot("DEFENSE", "ATTAQUE")
            if slot is not None:
                self.send_piocher(slot)
            else:
                self.end_turn()