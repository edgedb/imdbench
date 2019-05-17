import {Entity, PrimaryColumn, Column, OneToMany} from "typeorm";
import {Cast} from './Cast'
import {Directors} from './Directors'


@Entity()
export class Person {

    // PrimaryGeneratedColumn ignores id even if specified
    @PrimaryColumn()
    id: number;

    @Column()
    first_name: string;

    @Column()
    middle_name: string;

    @Column()
    last_name: string;

    @Column()
    bio: string;

    @Column()
    image: string;

    @OneToMany(type => Directors, directors => directors.person)
    directed: Directors[];

    @OneToMany(type => Cast, cast => cast.person)
    acted_in: Cast[];

    get_full_name() {
        return (
            this.middle_name ?
            this.first_name + ' ' + this.middle_name + ' ' + this.last_name
            :
            this.first_name + ' ' + this.last_name
        );
    }
}
