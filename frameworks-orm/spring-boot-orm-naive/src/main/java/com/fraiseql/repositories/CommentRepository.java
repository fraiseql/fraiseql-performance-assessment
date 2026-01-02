package com.fraiseql.repositories;

import com.fraiseql.entities.Comment;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface CommentRepository extends JpaRepository<Comment, Long> {

    List<Comment> findByPostId(Long postId);

    List<Comment> findByAuthorId(Long authorId);

    // NAIVE: No fetch joins - accessing relationships will cause N+1 queries!
    // When you call comment.getAuthor() or comment.getPost(), it will execute separate queries
}