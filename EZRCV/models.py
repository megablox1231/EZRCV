import sqlalchemy as sa
import sqlalchemy.orm as so
from EZRCV import db


class Ballot(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(64))
    display_records: so.Mapped[bool]
    allow_name: so.Mapped[bool]

    entries: so.WriteOnlyMapped['Entry'] = so.relationship(back_populates='ballot')
    votes: so.WriteOnlyMapped['Voter'] = so.relationship(back_populates='ballot')

    def __repr__(self):
        return '<Ballot {}: Name({})>'.format(self.id, self.name)


class Entry(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    ballot_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Ballot.id))
    name: so.Mapped[str] = so.mapped_column(sa.String(64))
    votes: so.Mapped[int] = so.mapped_column(sa.INT, default=0)

    ballot: so.Mapped[Ballot] = so.relationship(back_populates='entries')

    def __repr__(self):
        return '<Entry {}: Name({}), votes({})>'.format(self.id, self.name, self.votes)


class Voter(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    ballot_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Ballot.id))
    name: so.Mapped[str] = so.mapped_column(sa.String(64))
    vote: so.Mapped[str] = so.mapped_column(sa.TEXT(65000))

    ballot: so.Mapped[Ballot] = so.relationship(back_populates='votes')

    def __repr__(self):
        return '<Vote {}: Name({}): {}>'.format(self.id, self.name, self.vote)
