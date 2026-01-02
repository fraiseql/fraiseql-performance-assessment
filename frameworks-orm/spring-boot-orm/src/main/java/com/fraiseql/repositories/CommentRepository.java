package com.fraiseql.repositories;

import com.fraiseql.entities.Comment;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.jpa.repository.QueryHints;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import javax.persistence.QueryHint;
import java.util.List;

@Repository
public interface CommentRepository extends JpaRepository<Comment, Long> {

    List<Comment> findByPostId(Long postId);

    List<Comment> findByAuthorId(Long authorId);

    // Optimized query with fetch joins
    @Query("SELECT c FROM Comment c LEFT JOIN FETCH c.author LEFT JOIN FETCH c.post WHERE c.id = :id")
    @QueryHints(@QueryHint(name = "org.hibernate.fetchSize", value = "20"))
    Comment findByIdWithAuthorAndPost(@Param("id") Long id);

    // Batch loading
    @Query("SELECT c FROM Comment c LEFT JOIN FETCH c.author LEFT JOIN FETCH c.post WHERE c.id IN :ids")
    @QueryHints(@QueryHint(name = "org.hibernate.fetchSize", value = "20"))
    List<Comment> findAllByIdWithAuthorAndPost(@Param("ids") List<Long> ids);

    // Comments for post with authors
    @Query("SELECT c FROM Comment c LEFT JOIN FETCH c.author WHERE c.post.id = :postId ORDER BY c.createdAt ASC")
    @QueryHints(@QueryHint(name = "org.hibernate.fetchSize", value = "20"))
    List<Comment> findByPostIdWithAuthor(@Param("postId") Long postId);
}