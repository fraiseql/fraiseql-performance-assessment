package com.fraiseql.repositories;

import com.fraiseql.entities.Post;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.jpa.repository.QueryHints;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import javax.persistence.QueryHint;
import java.util.List;

@Repository
public interface PostRepository extends JpaRepository<Post, Long> {

    List<Post> findByAuthorId(Long authorId);

    // Optimized query with fetch join for author
    @Query("SELECT p FROM Post p LEFT JOIN FETCH p.author WHERE p.id = :id")
    @QueryHints(@QueryHint(name = "org.hibernate.fetchSize", value = "20"))
    Post findByIdWithAuthor(@Param("id") Long id);

    // Batch loading with optimized fetch
    @Query("SELECT p FROM Post p LEFT JOIN FETCH p.author WHERE p.id IN :ids")
    @QueryHints(@QueryHint(name = "org.hibernate.fetchSize", value = "20"))
    List<Post> findAllByIdWithAuthor(@Param("ids") List<Long> ids);

    // Optimized query with author and comments
    @Query("SELECT p FROM Post p LEFT JOIN FETCH p.author LEFT JOIN FETCH p.comments WHERE p.id = :id")
    @QueryHints(@QueryHint(name = "org.hibernate.fetchSize", value = "20"))
    Post findByIdWithAuthorAndComments(@Param("id") Long id);

    // Paginated query with fetch joins
    @Query("SELECT p FROM Post p LEFT JOIN FETCH p.author ORDER BY p.createdAt DESC")
    @QueryHints(@QueryHint(name = "org.hibernate.fetchSize", value = "20"))
    List<Post> findAllWithAuthorOrderByCreatedAtDesc();
}