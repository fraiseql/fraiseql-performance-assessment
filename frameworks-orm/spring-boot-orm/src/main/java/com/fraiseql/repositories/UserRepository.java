package com.fraiseql.repositories;

import com.fraiseql.entities.User;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.jpa.repository.QueryHints;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import javax.persistence.QueryHint;
import java.util.List;
import java.util.Optional;

@Repository
public interface UserRepository extends JpaRepository<User, Long> {

    Optional<User> findByUsername(String username);

    // Optimized query with fetch join to prevent N+1 queries
    @Query("SELECT u FROM User u LEFT JOIN FETCH u.posts WHERE u.id = :id")
    @QueryHints(@QueryHint(name = "org.hibernate.fetchSize", value = "20"))
    Optional<User> findByIdWithPosts(@Param("id") Long id);

    // Batch loading with optimized fetch
    @Query("SELECT DISTINCT u FROM User u LEFT JOIN FETCH u.posts WHERE u.id IN :ids")
    @QueryHints(@QueryHint(name = "org.hibernate.fetchSize", value = "20"))
    List<User> findAllByIdWithPosts(@Param("ids") List<Long> ids);

    // Optimized query for user with posts and comments
    @Query("SELECT u FROM User u LEFT JOIN FETCH u.posts p LEFT JOIN FETCH p.comments WHERE u.id = :id")
    @QueryHints(@QueryHint(name = "org.hibernate.fetchSize", value = "20"))
    Optional<User> findByIdWithPostsAndComments(@Param("id") Long id);
}