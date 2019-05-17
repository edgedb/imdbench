import {Entity, PrimaryGeneratedColumn, Column, ManyToOne,
        JoinColumn, Index} from "typeorm";
import {Person} from './Person'
import {Movie} from './Movie'


@Entity()
export class Directors {

    @PrimaryGeneratedColumn()
    id: number;

    @Column()
    list_order: number;

    @Column({select: false})
    @Index()
    person_id: number;

    @Column({select: false})
    @Index()
    movie_id: number;

    @ManyToOne(type => Person, person => person.directed)
    @JoinColumn({name: 'person_id'})
    person: Person

    @ManyToOne(type => Movie, movie => movie.directors)
    @JoinColumn({name: 'movie_id'})
    movie: Movie
}
