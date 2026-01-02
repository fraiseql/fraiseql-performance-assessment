package com.fraiseql.repositories;

import com.fraiseql.entities.User;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface UserRepository extends JpaRepository<User, Long> {

    Optional<User> findByUsername(String username);

    // NAIVE: No fetch joins - accessing relationships will cause N+1 queries!
    // When you call user.getPosts(), it will execute a separate query for each user
}