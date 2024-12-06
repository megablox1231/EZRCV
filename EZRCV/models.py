import sqlalchemy as sa
import sqlalchemy.orm as so
from EZRCV import db
from collections import deque
import itertools

import pandas as pd


class Ballot(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(64))
    display_records: so.Mapped[bool]
    allow_name: so.Mapped[bool]

    entries: so.WriteOnlyMapped['Entry'] = so.relationship(back_populates='ballot')
    votes: so.WriteOnlyMapped['Voter'] = so.relationship(back_populates='ballot')

    def __repr__(self):
        return '<Ballot {}: Name({})>'.format(self.id, self.name)

    def to_dict(self):
        entries = get_ballot_entries(self.id)

        data = {
            'id': self.id,
            'name': self.name,
            'display_records': self.display_records,
            'allow_name': self.allow_name,
            'entries': entries
        }
        return data


class Entry(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    ballot_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Ballot.id))
    name: so.Mapped[str] = so.mapped_column(sa.String(64))

    ballot: so.Mapped[Ballot] = so.relationship(back_populates='entries')

    def __repr__(self):
        return '<Entry {}: Name({}), BallotID({})>'.format(self.id, self.name, self.ballot_id)


class Voter(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    ballot_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Ballot.id))
    name: so.Mapped[str] = so.mapped_column(sa.String(64))
    vote: so.Mapped[str] = so.mapped_column(sa.TEXT(65000))

    ballot: so.Mapped[Ballot] = so.relationship(back_populates='votes')

    def __repr__(self):
        return '<Vote {}: Name({}): {}>'.format(self.id, self.name, self.vote)


def get_ballot_entries(ballot_id):
    results = db.session.scalars(sa.select(Entry).where(Entry.ballot_id == ballot_id)).fetchall()
    candidates = {candidate.id: candidate.name for candidate in results}
    return candidates


def calculate_winners(ballot_id):
    """Calculates a winner to the results template using the instant-runoff voting method."""
    ballot_opts = db.session.scalar(sa.select(Ballot).where(Ballot.id == ballot_id))

    # rankings(votes) are stored as a list of deques with most preferred candidates on top
    voters = db.session.scalars(sa.select(Voter).where(Voter.ballot_id == ballot_id)).fetchall()
    rankings = [deque(int(entry) for entry in reversed(voter.vote.split(" "))) for voter in voters]

    if len(rankings) == 0:
        return {
            "ballot_opts": ballot_opts
        }

    win_threshold = len(rankings) / 2
    # print(rankings)
    # candidates points are stored as a dictionary of id keys and vote deque array values
    # points are determined by the length of these arrays
    cands = db.session.scalars(sa.select(Entry).where(Entry.ballot_id == ballot_id)).fetchall()
    cand_pts = {cand.id: [] for cand in cands}
    for ranking in rankings:
        cand_pts[ranking.pop()].append(ranking)

    rounds_df = pd.DataFrame({'Candidate IDs': [cand.id for cand in cands],
                              'Candidate Name': [cand.name for cand in cands]})
    round_num = 1

    while True:
        cand_results = list(cand_pts.items())
        cand_results.sort(key=lambda tup: len(tup[1]), reverse=True)

        extract_round_data(cand_pts, rounds_df, round_num)

        if len(cand_results[0][1]) > win_threshold:
            # the top candidate got more than 50% of the vote
            result = [db.session.scalar(sa.select(Entry.name).where(Entry.id == cand_results[0][0]))]
            break
        else:
            elim_threshold = len(cand_results[-1][1])
            elim_count = 0

            for cand in reversed(cand_results):
                if len(cand[1]) > elim_threshold:
                    break
                elim_count += 1

            if elim_count == len(cand_results):
                # the remaining candidates have the same number of votes
                # print('its a tie')
                result = db.session.scalars(
                    sa.select(Entry.name).where(Entry.id.in_(
                        [cand[0] for cand in
                         itertools.islice(cand_results, len(cand_results)-elim_count, len(cand_results))]))).fetchall()
                break
            else:
                for cand in itertools.islice(cand_results, len(cand_results) - elim_count, len(cand_results)):
                    for ranking in cand_pts.pop(cand[0]):
                        if ranking[-1] in cand_pts:
                            cand_pts[ranking.pop()].append(ranking)
        round_num += 1

    # splitting record votes and replacing with cand names for use in html
    cand_dict = {}
    for cand in cands:
        cand_dict[str(cand.id)] = cand.name
    for record in voters:
        record.vote = [cand_dict[cand] for cand in record.vote.split(" ")]

    results = {
        "rounds_df": rounds_df,
        "round_num": round_num,
        "win_threshold": win_threshold,
        "result": result,
        "voters": voters,
        "ballot_opts": ballot_opts
    }

    return results


def extract_round_data(cand_pts, rounds_df, round_num):
    """Along with candidate name and ID, rounds_df adds a column for each round's first-choice vote totals."""
    rounds_df['Round ' + str(round_num) + ' First-Choice Votes'] = [len(cand_pts.get(cand_id, []))
                                                                    for cand_id in rounds_df['Candidate IDs']]
