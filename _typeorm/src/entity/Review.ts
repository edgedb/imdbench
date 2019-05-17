import {Entity, PrimaryColumn, Column, ManyToOne, JoinColumn,
        Index} from "typeorm";
import {User} from './User'
import {Movie, MovieView} from './Movie'


@Entity()
export class Review {

    // PrimaryGeneratedColumn ignores id even if specified
    @PrimaryColumn()
    id: number;

    @Column()
    body: string;

    @Column()
    rating: number;

    @Column()
    creation_time: Date;

    @Column({select: false})
    @Index()
    movie_id: number;

    @Column({select: false})
    @Index()
    author_id: number;

    @ManyToOne(type => User, user => user.reviews)
    @JoinColumn({name: 'author_id'})
    author: User

    @ManyToOne(type => Movie, movie => movie.reviews)
    @JoinColumn({name: 'movie_id'})
    movie: Movie
}
