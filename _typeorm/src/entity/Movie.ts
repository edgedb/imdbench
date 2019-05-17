import {Entity, PrimaryColumn, Column, OneToMany,
        ViewEntity, ViewColumn, Connection} from "typeorm";
import {Review} from './Review'
import {Cast} from './Cast'
import {Directors} from './Directors'


@Entity()
export class Movie {

    // PrimaryGeneratedColumn ignores id even if specified
    @PrimaryColumn()
    id: number;

    @Column()
    image: string;

    @Column()
    title: string;

    @Column()
    year: number;

    @Column()
    description: string;

    @OneToMany(type => Review, review => review.movie)
    reviews: Review[];

    @OneToMany(type => Directors, directors => directors.movie)
    directors: Directors[];

    @OneToMany(type => Cast, cast => cast.movie)
    cast: Cast[];
}


@ViewEntity({
    expression: (connection: Connection) => connection.createQueryBuilder()
        .select(["id", "image", 'title', 'year', 'description'])
        .addSelect(subQuery => {
            return subQuery
                .addSelect("avg(review.rating)", 'avg_rating')
                .from(Review, "review")
                .where('review.movie_id = movie.id');
            }, "avg_rating")
        .from(Movie, "movie")
})
export class MovieView {

    // PrimaryGeneratedColumn ignores id even if specified
    @ViewColumn()
    id: number;

    @ViewColumn()
    image: string;

    @ViewColumn()
    title: string;

    @ViewColumn()
    year: number;

    @ViewColumn()
    description: string;

    @ViewColumn()
    avg_rating: number;
}
