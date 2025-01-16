


def normalize_training_proposals(proposals):
    normalized_proposals = []
    for proposal in proposals:
        if isinstance(proposal, dict):
            # Konwersja słownika na string w formacie: "nazwa: {nazwa}, szczegóły: {szczegóły}"
            details = ", ".join(f"{key}: {value}" for key, value in proposal.items())
            normalized_proposals.append(details)
        elif isinstance(proposal, str):
            # Jeśli to string, pozostaw bez zmian
            normalized_proposals.append(proposal)
        else:
            # Jeśli jest inny typ (dla bezpieczeństwa)
            raise ValueError(f"Nieobsługiwany typ danych w propozycjach szkoleń: {type(proposal)}")
    return normalized_proposals