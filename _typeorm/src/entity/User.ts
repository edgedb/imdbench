import {Entity, PrimaryColumn, Column, OneToMany} from "typeorm";
import {Review} from './Review'


@Entity()
export class User {

    // PrimaryGeneratedColumn ignores id even if specified
    @PrimaryColumn()
    id: number;

    @Column()
    name: string;

    @Column()
    image: string;

    @OneToMany(type => Review, review => review.author)
    reviews: Review[];
}
